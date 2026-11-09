# Symulacja Kamery Cofania – Parking

Interaktywna symulacja kamery cofania w samochodzie osobowym, napisana w Pythonie z użyciem biblioteki **pygame**.  
Program odwzorowuje widok z kamery cofania (perspektywa 3D) oraz widok z góry na parking.

---

## Zrzut ekranu

```
┌─────────────────────────────┬──────────────┐
│                             │   Mapa       │
│   Widok kamery cofania      │   z góry     │
│   (perspektywa 3D)          │   (top-down) │
│                             │              │
└─────────────────────────────┴──────────────┘
```

---

## Wymagania

- Python 3.8+
- pygame 2.0+

```bash
pip install pygame
```

---

## Uruchomienie

```bash
python3 backup_camera_sim.py
```

---

## Sterowanie

| Klawisz | Akcja |
|---------|-------|
| `W` / `↑` | Jedź do przodu |
| `S` / `↓` | Cofaj |
| `A` / `←` | Skręć w lewo |
| `D` / `→` | Skręć w prawo |
| `R` | Zresetuj pozycję samochodu |
| `ESC` | Wyjście |

---

## Opis działania

### Podział ekranu

Okno (1400 × 750 px) dzieli się na dwa panele:

- **Lewy panel (900 × 750 px)** – widok kamery cofania  
- **Prawy panel (500 × 750 px)** – mapa parkingu z góry

### Widok kamery cofania (lewy panel)

Kamera jest zamocowana z tyłu samochodu i patrzy w kierunku ruchu wstecznego.  
Renderowanie używa projekcji perspektywicznej na rzut ekranu:

- **Pole widzenia**: 160° poziomo
- **Horyzont**: dzieli ekran na niebo (gradient błękitny) i ziemię (gradient szary)
- **Obiekty na parkingu** są rzutowane z przestrzeni 3D na ekran przy użyciu wzoru głębokości:
  `sy = HORIZON_Y + GROUND_K / depth`
- **Zaparkowane samochody** renderowane jako bryły 3D (sześcian z oknami i dachówką), każda ściana rysowana osobno z cieniowaniem kierunkowym
- **Piesi** rysowani jako wieloczęściowe postacie (głowa, tułów, nogi, ręce) z animacją chodu
- **Linie parkingowe** i oznaczenia jezdni rzutowane na podłoże
- **HUD z odległością** – kolorowy wskaźnik na dole ekranu pokazuje odległość do najbliższej przeszkody:
  - 🟢 Zielony: > 4 m – bezpiecznie
  - 🟡 Żółty: 2–4 m – uwaga
  - 🟠 Pomarańczowy: 1–2 m – ostrożnie
  - 🔴 Czerwony: < 1 m – niebezpiecznie
  - 🔴 **STOP!** – < 0,5 m – kolizja grozi

### Mapa z góry (prawy panel)

Widok z lotu ptaka na cały parking, wyśrodkowany na samochodzie gracza:

- Zaparkowane samochody (kolorowe prostokąty z zarysem)
- Drzewa (zielone okręgi z cieniem)
- Lampy parkingowe
- Piesi (kolorowe kółka)
- Stożek widzenia kamery cofania (żółty trójkąt 160°)
- Samochód gracza (czerwony prostokąt)

### Fizyka i kolizje

**Ruch samochodu**:
- Prędkość liniowa z tarciem (zwalnianie po puszczeniu gazu)
- Skręcanie tylko przy prędkości > 0 (jak prawdziwy samochód)
- Blokada na granicach świata

**Kolizje samochód ↔ zaparkowane auto**:
- Detekcja kolizji metodą **SAT** (Separating Axis Theorem) na zorientowanych prostokątach (OBB)
- Wyznaczenie **MTV** (Minimum Translation Vector) – samochód jest odsuwany bez przenikania
- Przy kolizji: odskoczenie, podświetlenie na czerwono

**Kolizje samochód ↔ pieszy**:
- Prosta detekcja AABB/promień
- Pieszy zatrzymuje się, miga na czerwono, a po chwili **znika** (znika z obu widoków)

### Świat parkingu

| Element | Liczba |
|---------|--------|
| Miejsca parkingowe | 20 (w 2 rzędach) |
| Zajęte miejsca (losowe) | ~25 samochodów |
| Kolory samochodów | Paleta 14 żywych kolorów |
| Piesi | 14 postaci |
| Drzewa | 42 |
| Lampy | 12 |

Układ parkingu jest generowany deterministycznie (stałe ziarna losowe), więc wygląda tak samo przy każdym uruchomieniu.

---

## Struktura kodu (`backup_camera_sim.py`)

| Fragment | Opis |
|----------|------|
| `Car` | Klasa samochodu gracza (fizyka, OBB) |
| `ParkedCar` | Klasa zaparkowanego auta (OBB, stan kolizji) |
| `Pedestrian` | Klasa pieszego (ruch, animacja, stan życia) |
| `world_to_cam` | Projekcja perspektywiczna z kontrolą FOV |
| `_project_nc` | Projekcja perspektywiczna bez ograniczenia kąta FOV |
| `cam_ground` | Rzutowanie punktu z płaszczyzny ziemi |
| `_cam_box` | Renderowanie 3D bryły samochodu (per-face quads) |
| `_cam_pedestrian` | Renderowanie postaci pieszego |
| `sat_collide` | Detekcja kolizji OBB metodą SAT + MTV |
| `check_car_collisions` | Pętla kolizji gracza z zaparkowanymi autami |
| `nearest_rear_distance` | Pomiar odległości do przeszkody w stożku kamery |
| `draw_camera_view` | Renderowanie lewego panelu (kamera 3D) |
| `draw_topdown` | Renderowanie prawego panelu (widok z góry) |
| `main` | Główna pętla gry |
