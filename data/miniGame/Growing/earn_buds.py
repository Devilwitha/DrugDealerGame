# -*- coding: utf-8 -*-
# earn_buds.py (Angepasst von pygame_minigame_template_v2...)
# Gibt die gesammelte Menge Weed am Ende über print() aus.
# Korrigierte `return`-Anweisung in `run_minigame_template`.
# Korrigierte Position von print(earned_amount) im __main__ Block.
import pygame
import sys
import os
import traceback
import time
import random

# --- Android Immersive Mode & Platform Detection ---
is_android = False
try:
    from jnius import autoclass, cast, PythonJavaClass, java_method
    print("DEBUG (earn_buds): Pyjnius importiert.")
    Build = autoclass('android.os.Build$VERSION')
    sdk_int = Build.SDK_INT
    if sdk_int > 0:
        is_android = True
        print(f"DEBUG (earn_buds): Android erkannt (SDK: {sdk_int}).")
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        assert activity is not None
        View = autoclass('android.view.View')
        Window = autoclass('android.view.Window')
        WindowManager = autoclass('android.view.WindowManager$LayoutParams')
        flags = ( View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY )
        class SetUiVisibilityRunnablePJC(PythonJavaClass):
            __javainterfaces__ = ['java/lang/Runnable']
            def __init__(self, a, f): super().__init__(); self.a = a; self.f = f
            @java_method('()V')
            def run(self):
                try: w = self.a.getWindow(); d = w.getDecorView(); d.setSystemUiVisibility(self.f); w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                except Exception as e: print(f"FEHLER (Runnable): {e}"); traceback.print_exc()
        runnable = SetUiVisibilityRunnablePJC(activity, flags)
        if activity: activity.runOnUiThread(runnable); print("DEBUG (earn_buds): Runnable Immersive gestartet.")
        else: print("WARNUNG (earn_buds): Activity nicht gefunden trotz Android-Erkennung.")
    else: print("INFO (earn_buds): Nicht Android (SDK <= 0)"); is_android = False
except ImportError: print("INFO (earn_buds): Pyjnius nicht gefunden. Nehme an, es ist nicht Android."); is_android = False
except Exception as e: print(f"FEHLER oder Info (earn_buds): Immersive Mode fehlgeschlagen oder nicht Android: {e}"); is_android = False
# --- Ende Android ---


# --- Farben ---
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150); TEMPLATE_COLOR_1 = (0, 100, 200)

# --- Dateinamen für Assets ---
background_image_filename = "ern_plant_weed_normal.png"
clickable_element_filename = "ern_bud_weed_normal.png"
back_button_bg_filename = "back_button_bg.png"
back_button_hover_filename = "back_button_hover.png"
sound_effect_1_filename = "cut_plant.wav"

# --- Klasse für klickbare/fallende Elemente ---
class FallingElement:
    def __init__(self, ref_x, ref_y, ref_w, ref_h, screen_width, screen_height, element_size_scaled, image=None):
        self.ref_x = ref_x; self.ref_y = ref_y; self.ref_screen_w = ref_w; self.ref_screen_h = ref_h
        self.screen_w = screen_width; self.screen_h = screen_height
        scale_x = self.screen_w / self.ref_screen_w; scale_y = self.screen_h / self.ref_screen_h
        self.size = element_size_scaled
        self.x = int(self.ref_x * scale_x); self.y = int(self.ref_y * scale_y)
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        self.image = image
        if self.image:
            try: self.image = pygame.transform.smoothscale(self.image, (self.size, self.size))
            except pygame.error as e: print(f"WARNUNG: Skalieren fehlgeschlagen: {e}"); self.image = None
        self.fallback_surface = None
        if not self.image:
             self.fallback_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA); self.fallback_surface.fill(TEMPLATE_COLOR_1 + (255,))
        self.state = "visible"; self.fall_start_time = 0.0; self.current_y = float(self.y); self.alpha = 255.0
        self.FALL_SPEED = 200; self.FADE_DURATION = 2.0

    def start_fall(self):
        if self.state == "visible": self.state = "falling"; self.fall_start_time = time.time(); self.current_y = float(self.y); self.alpha = 255.0

    def update(self, dt):
        if self.state == "falling":
            elapsed_time = time.time() - self.fall_start_time; self.current_y += self.FALL_SPEED * dt; self.rect.y = int(self.current_y)
            if elapsed_time < self.FADE_DURATION: self.alpha = max(0.0, 255.0 * (1.0 - (elapsed_time / self.FADE_DURATION)))
            else: self.alpha = 0.0; self.state = "faded"
            current_alpha_int = int(self.alpha)
            if self.image:
                try: temp_image = self.image.copy(); temp_image.set_alpha(current_alpha_int); self.current_image_instance = temp_image
                except (AttributeError, pygame.error): pass
            elif self.fallback_surface:
                try: self.fallback_surface.set_alpha(current_alpha_int)
                except pygame.error: pass

    def draw(self, screen):
        if self.state == "visible":
            if self.image: screen.blit(self.image, self.rect.topleft)
            elif self.fallback_surface: self.fallback_surface.set_alpha(255); screen.blit(self.fallback_surface, self.rect.topleft)
        elif self.state == "falling":
            if self.alpha > 0:
                if self.image and hasattr(self, 'current_image_instance'): screen.blit(self.current_image_instance, (self.rect.x, int(self.current_y)))
                elif self.fallback_surface: screen.blit(self.fallback_surface, (self.rect.x, int(self.current_y)))
# --- Ende FallingElement Klasse ---

# --- Hauptfunktion des Minispiels ---
def run_minigame_template(screen_surface, start_resource1, start_resource2, start_score, id1, id2):
    """ Template für ein Pygame Minispiel mit fallenden Elementen und Sammeln von Ressource 1. """
    screen = screen_surface
    actual_screen_size = screen.get_size()
    screen_width, screen_height = actual_screen_size
    screen_center_x = screen_width // 2; screen_center_y = screen_height // 2
    print(f"DEBUG (earn_buds): Nutze Screen-Größe: {actual_screen_size}")

    current_weed = start_resource1; current_other_resource = start_resource2; current_score = start_score
    weed_identifier = id1; other_identifier = id2
    print(f"DEBUG (earn_buds): Startwerte: {weed_identifier}={current_weed}, {other_identifier}={current_other_resource}, Score={current_score}")
    game_state = "running"
    ref_w = 800.0; ref_h = 600.0; FONT_SIZE_REF_H = 600.0

    sound_effect_1 = None; mixer_ok = False
    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024); print("DEBUG (earn_buds): Mixer initialisiert."); mixer_ok = True
        except pygame.error as e: print(f"WARNUNG (earn_buds): Mixer fehlgeschlagen: {e}")
    else: print("DEBUG (earn_buds): Mixer war bereits initialisiert."); mixer_ok = True

    try: script_dir_game = os.path.dirname(os.path.abspath(__file__))
    except NameError: script_dir_game = os.path.abspath(".")
    project_root_folder = os.path.abspath(os.path.join(script_dir_game, "..", "..", ".."))
    data_subfolder = "data"; image_folder_rel = os.path.join(data_subfolder, "bilder"); sound_folder_rel = os.path.join(data_subfolder, "sounds")
    image_folder_abs = os.path.normpath(os.path.join(project_root_folder, image_folder_rel)); sound_folder_abs = os.path.normpath(os.path.join(project_root_folder, sound_folder_rel))
    print(f"DEBUG (earn_buds): Script Dir: {script_dir_game}"); print(f"DEBUG (earn_buds): Project Root (berechnet): {project_root_folder}"); print(f"DEBUG (earn_buds): Image folder (abs): {image_folder_abs}"); print(f"DEBUG (earn_buds): Sound folder (abs): {sound_folder_abs}")

    if is_android:
        try:
             from jnius import autoclass, cast, PythonJavaClass, java_method
             PythonActivity = autoclass('org.kivy.android.PythonActivity'); activity = PythonActivity.mActivity; View = autoclass('android.view.View'); Window = autoclass('android.view.Window'); WindowManager = autoclass('android.view.WindowManager$LayoutParams')
             flags = ( View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY )
             class SetUiVisibilityRunnablePJCInner(PythonJavaClass):
                 __javainterfaces__ = ['java/lang/Runnable']; 
                 def __init__(self, a, f): super().__init__(); self.a = a; self.f = f
                 @java_method('()V')
                 def run(self):
                     try: w = self.a.getWindow(); d = w.getDecorView(); d.setSystemUiVisibility(self.f); w.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
                     except Exception as e: print(f"FEHLER (Runnable Inner): {e}"); traceback.print_exc()
             if activity: runnable_inner = SetUiVisibilityRunnablePJCInner(activity, flags); activity.runOnUiThread(runnable_inner); print("DEBUG (earn_buds Android Inner): Runnable Immersive gestartet.")
             else: print("WARNUNG (earn_buds Android Inner): Keine Activity gefunden.")
        except Exception as e: print(f"FEHLER (earn_buds Android Inner): Immersive Mode: {e}")

    scaled_background_image = None; use_background_image = False; background_path = os.path.join(image_folder_abs, background_image_filename)
    try: loaded_bg = pygame.image.load(background_path).convert(); scaled_background_image = pygame.transform.smoothscale(loaded_bg, actual_screen_size); use_background_image = True; print(f"DEBUG (earn_buds): Hintergrund '{background_image_filename}' geladen.")
    except Exception as e: print(f"WARNUNG (earn_buds): Hintergrund '{background_path}' laden fehlgeschlagen: {e}.")

    clickable_element_image = None; element_image_path = os.path.join(image_folder_abs, clickable_element_filename)
    try: clickable_element_image = pygame.image.load(element_image_path).convert_alpha(); print(f"DEBUG (earn_buds): Element Bild '{clickable_element_filename}' geladen.")
    except Exception as e: print(f"WARNUNG (earn_buds): Element Bild '{element_image_path}' laden fehlgeschlagen: {e}.")

    scaled_back_button_bg = None; scaled_back_button_hover = None; use_back_button_images = False
    BACK_BUTTON_WIDTH_PERCENT,BACK_BUTTON_HEIGHT_PERCENT,BASE_BACK_FONT_SIZE = 0.20,0.08,24
    back_button_width = int(screen_width*BACK_BUTTON_WIDTH_PERCENT); back_button_height = int(screen_height*BACK_BUTTON_HEIGHT_PERCENT)
    back_button_y = 10; back_button_rect = pygame.Rect((screen_width-back_button_width)//2,back_button_y,back_button_width,back_button_height)
    back_bg_path = os.path.join(image_folder_abs,back_button_bg_filename); back_hover_path = os.path.join(image_folder_abs,back_button_hover_filename)
    try:
        img_bg=pygame.image.load(back_bg_path).convert_alpha(); img_hover=pygame.image.load(back_hover_path).convert_alpha()
        scaled_back_button_bg=pygame.transform.smoothscale(img_bg,back_button_rect.size); scaled_back_button_hover=pygame.transform.smoothscale(img_hover,back_button_rect.size)
        use_back_button_images=True; print(f"DEBUG (earn_buds): Zurück-Buttons geladen.")
    except Exception as e: print(f"WARNUNG (earn_buds): Zurück-Buttons laden/skalieren fehlgeschlagen: {e}")

    BASE_INFO_FONT_SIZE = 24; info_font_size = max(12,int(screen_height*(BASE_INFO_FONT_SIZE/FONT_SIZE_REF_H)))
    info_font = None; 
    try: info_font = pygame.font.SysFont("arial", info_font_size)
    except: info_font = pygame.font.Font(None, info_font_size)
    if not info_font: info_font = pygame.font.Font(None, 24); info_font_size = 24

    BASE_BUTTON_FONT_SIZE = 20; button_font_size = max(12,int(screen_height*(BASE_BUTTON_FONT_SIZE/FONT_SIZE_REF_H)))
    button_font = None; 
    try: button_font = pygame.font.SysFont("arial", button_font_size)
    except: button_font = pygame.font.Font(None, button_font_size)
    if not button_font: button_font = pygame.font.Font(None, 20); button_font_size = 20

    sound_path_1 = os.path.join(sound_folder_abs, sound_effect_1_filename)
    if mixer_ok:
        try: sound_effect_1 = pygame.mixer.Sound(sound_path_1); sound_effect_1.set_volume(0.7); print(f"DEBUG (earn_buds): Sound 1 '{sound_effect_1_filename}' geladen.")
        except Exception as e: print(f"WARNUNG (earn_buds): Sound 1 '{sound_path_1}' laden fehlgeschlagen: {e}"); sound_effect_1 = None

    clickable_elements = []
    element_ref_coords = [(308,74),(430,40),(380,108),(444,208),(310,245),(419,356),(348,355),(379,239)]
    ELEMENT_REF_SIZE = 30; element_size_scaled = max(10, int(ELEMENT_REF_SIZE*(screen_height/ref_h)))
    for ref_x, ref_y in element_ref_coords:
        element = FallingElement(ref_x,ref_y,ref_w,ref_h,screen_width,screen_height,element_size_scaled,clickable_element_image.copy() if clickable_element_image else None)
        clickable_elements.append(element)

    clock = pygame.time.Clock(); last_time = time.time()
    running = True
    while running:
        current_time = time.time(); dt = min(current_time - last_time, 0.1); last_time = current_time
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: print("WARNUNG (earn_buds): QUIT Event."); running = False; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False; continue
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button_rect and back_button_rect.collidepoint(event.pos): running = False; continue
                    clicked_element = False
                    for element in reversed(clickable_elements):
                        if element.state == "visible" and element.rect.collidepoint(event.pos):
                            print(f"DEBUG: Element bei ({element.ref_x},{element.ref_y}) geklickt.")
                            element.start_fall(); current_weed += 1; print(f"DEBUG: {weed_identifier} erhöht auf {current_weed}")
                            current_score += 5;
                            if sound_effect_1: sound_effect_1.play()
                            clicked_element = True; break

        if game_state == "running":
            active_elements = 0
            for element in clickable_elements:
                if element.state != "faded": element.update(dt)
                if element.state != "faded": active_elements += 1
            if active_elements == 0 and len(clickable_elements) > 0:
                 print("INFO: Alle Elemente geklickt/verschwunden.")
                 running = False # Beende das Minispiel

        if use_background_image and scaled_background_image: screen.blit(scaled_background_image, (0,0))
        else: screen.fill(WHITE)
        for element in clickable_elements: element.draw(screen)
        if info_font:
             text_y_start = back_button_rect.bottom+10 if back_button_rect else 10; text_x_start = 10
             score_text = info_font.render(f"Punkte: {current_score}", True, BLACK); screen.blit(score_text, (text_x_start, text_y_start))
             weed_text = info_font.render(f"{weed_identifier}: {current_weed}", True, BLACK); screen.blit(weed_text, (text_x_start, text_y_start+info_font_size+5))
        if back_button_rect:
            current_back_img = scaled_back_button_bg; is_hovering = back_button_rect.collidepoint(mouse_pos)
            if not use_back_button_images: btn_color = DARK_GRAY if is_hovering else GRAY; pygame.draw.rect(screen,btn_color,back_button_rect); pygame.draw.rect(screen,BLACK,back_button_rect,2)
            if use_back_button_images:
                if is_hovering and scaled_back_button_hover: current_back_img = scaled_back_button_hover
                elif scaled_back_button_bg: current_back_img = scaled_back_button_bg
                if current_back_img: screen.blit(current_back_img, back_button_rect.topleft)
            if not use_back_button_images and button_font: back_text_surf = button_font.render("Zurück",True,BLACK); back_text_rect = back_text_surf.get_rect(center=back_button_rect.center); screen.blit(back_text_surf,back_text_rect)

        pygame.display.flip()
        clock.tick(60)

    print(f"INFO (earn_buds): Minispiel-Schleife beendet.")
    # --- KORRIGIERTER RETURN WERT als Tupel ---
    return current_weed, current_other_resource, current_score
# --- Ende der run_minigame_template Funktion ---


# --- Standalone Code (angepasst für STDOUT Ausgabe und Renderer-Fix-Versuch) ---
if __name__ == "__main__":
    print("INFO: earn_buds.py wird eigenständig ausgeführt.")
    pygame.init()

    if not pygame.mixer.get_init():
        try: pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e: print(f"WARNUNG (earn_buds Init): Mixer fehlgeschlagen: {e}")

    standalone_screen = None
    try: _info = pygame.display.Info(); _sw = _info.current_w; _sh = _info.current_h
    except Exception: _sw = 800; _sh = 600

    try:
        print(f"INFO: Versuche pygame.display.set_mode(({_sw}, {_sh}))")
        # --- Vereinfachte Flags ---
        standalone_screen = pygame.display.set_mode((_sw, _sh))
        # --------------------------
        pygame.display.set_caption("Earn Buds Minigame")
    except pygame.error as e_display:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"FEHLER bei pygame.display.set_mode: {e_display}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        pygame.quit(); sys.exit(1)
    except Exception as e_generic_display:
        print(f"Unerwarteter Fehler bei Display-Initialisierung: {e_generic_display}")
        pygame.quit(); sys.exit(1)

    start_weed_sa = 0; start_res2_sa = 0; start_score_sa = 0
    id1_sa = "Weed"; id2_sa = "Res2"
    print(f"\n--- Starte Minispiel 'earn_buds' ---\n")
    earned_amount = 0; exit_code = 1 # Standard: Fehler

    try:
        # Führe die Hauptlogik aus
        final_weed, _, final_score = run_minigame_template(
            standalone_screen, start_weed_sa, start_res2_sa, start_score_sa, id1_sa, id2_sa
        )
        # Berechne die in DIESEM DURCHLAUF gesammelte Menge
        earned_amount = final_weed - start_weed_sa
        if earned_amount < 0: earned_amount = 0
        print(f"--- Minispiel 'earn_buds' beendet. Ergebnis: Score={final_score}, Weed Total={final_weed} (Geerntet={earned_amount}) ---")
        exit_code = 0 # Erfolg!
    except Exception as e_main:
        print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"FEHLER im Minispiel 'earn_buds': {e_main}")
        print(f"-------------------------------------"); traceback.print_exc()
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"); # exit_code bleibt 1
    finally:
        # Erst Pygame beenden und INFOs ausgeben
        print(f"INFO (earn_buds): pygame.quit() wird aufgerufen.")
        if pygame.get_init(): # Nur beenden, wenn initialisiert
             pygame.quit()
        print(f"INFO (earn_buds): sys.exit({exit_code}) wird aufgerufen.")

        # ----- WICHTIG: Gib die geerntete Menge auf STDOUT aus - GANZ AM ENDE -----
        if exit_code == 0: # Nur bei Erfolg die Menge ausgeben
            print(earned_amount) # <--- Diese Zeile gibt die Zahl für game.py aus
        # -------------------------------------------------------------------------

        sys.exit(exit_code) # Beende den Prozess mit dem korrekten Code
# --- Ende Standalone-Code ---