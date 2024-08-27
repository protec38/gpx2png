import gpxpy
import gpxpy.gpx
import matplotlib.pyplot as plt
import numpy as np
from tkinter import Tk, filedialog, colorchooser, Button, Label, Listbox, StringVar, Entry, MULTIPLE, simpledialog, BooleanVar, Checkbutton, messagebox
from geopy.distance import geodesic
from PIL import Image


class GPXFile:
    def __init__(self, filepath, color, interval_km):
        self.filepath = filepath
        self.color = color
        self.interval_km = interval_km


def validate_gpx(filepath):
    try:
        with open(filepath, 'r') as f:
            gpxpy.parse(f)
        return True
    except Exception as e:
        messagebox.showerror("Erreur de validation", f"Erreur lors de la validation du fichier GPX : {filepath}\n\n{e}")
        return False


def convert_gpx_to_png(gpx_files, output_file, transparent_background):
    plt.figure(figsize=(8, 8))
    all_lats, all_lons = [], []
    displayed_text_positions = []  # List to store positions of displayed texts

    for gpx_file in gpx_files:
        with open(gpx_file.filepath, 'r') as f:
            gpx = gpxpy.parse(f)

        lats, lons = [], []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    lats.append(point.latitude)
                    lons.append(point.longitude)

        max_distance = geodesic((min(lats), min(lons)), (max(lats), max(lons))).km
        linewidth = max(1, 8 / max_distance)  # Ajustement en fonction de la taille de la trace
        marker_size = max(10, 200 / max_distance)

        # Tracer les points sur la figure
        plt.plot(lons, lats, color=gpx_file.color, linewidth=linewidth)
        all_lats.extend(lats)
        all_lons.extend(lons)

        # Marquer le point de départ
        plt.scatter(lons[0], lats[0], color='green', marker='.', label="Départ", s=marker_size, zorder=5)
        plt.text(lons[0], lats[0], 'Départ', fontsize=3, color='green', verticalalignment='bottom')

        # Marquer le point d'arrivée
        plt.scatter(lons[-1], lats[-1], color='red', marker='+', s=marker_size * 2, label="Arrivée", zorder=5)
        plt.text(lons[-1], lats[-1], 'Arrivée', fontsize=3, color='red', verticalalignment='bottom')

        # Ajouter des marqueurs kilométriques
        distance_accumulee = 0
        last_marker_distance = 0
        start_point = (lats[0], lons[0])

        for i in range(1, len(lats)):
            current_point = (lats[i], lons[i])
            distance_accumulee += geodesic(start_point, current_point).km
            start_point = current_point

            if distance_accumulee - last_marker_distance >= gpx_file.interval_km:
                position = (lons[i], lats[i])

                # Vérifier si cette position est trop proche d'une autre
                if any(geodesic(position, prev_pos).m < 100 for prev_pos in displayed_text_positions):
                    # Décaler légèrement la position pour éviter le chevauchement
                    position = (lons[i] - 0.005, lats[i] + 0.001)
                
                displayed_text_positions.append(position)

                # Calculer la direction perpendiculaire
                if i > 0:
                    dx = lons[i] - lons[i - 1]
                    dy = lats[i] - lats[i - 1]
                    norm = np.sqrt(dx**2 + dy**2)
                    dx /= norm
                    dy /= norm

                    # Calculer le vecteur perpendiculaire
                    perp_dx = -dy
                    perp_dy = dx

                    # Tracer le trait perpendiculaire
                    plt.plot([lons[i] - perp_dx * 0.0005, lons[i] + perp_dx * 0.0005],
                             [lats[i] - perp_dy * 0.0005, lats[i] + perp_dy * 0.0005],
                             color=gpx_file.color, linewidth=linewidth)

                # Afficher le texte du kilométrage
                if distance_accumulee < 1:
                    plt.text(position[0], position[1], f'{int(distance_accumulee * 1000)}m', fontsize=9, color=gpx_file.color)
                else:
                    plt.text(position[0], position[1], f'{int(distance_accumulee)}km', fontsize=9, color=gpx_file.color)
                
                last_marker_distance = distance_accumulee

    # Masquer les axes
    plt.axis('off')

    # Obtenir les coins de la carte
    axes = plt.gca()
    min_lat, max_lat = axes.get_ylim()[0], axes.get_ylim()[1]
    min_lon, max_lon = axes.get_xlim()[0], axes.get_xlim()[1]

    # Afficher les coordonnées GPS des coins
    plt.text(min_lon, max_lat, f"{max_lat:.15f};{min_lon:.15f}",
             fontsize=5, color='#0f0f0f20', ha='left', va='top')
    plt.text(max_lon, max_lat, f"{max_lat:.15f};{max_lon:.15f}",
             fontsize=5, color='#0f0f0f20', ha='right', va='top')
    plt.text(min_lon, min_lat, f"{min_lat:.15f};{min_lon:.15f}",
             fontsize=5, color='#0f0f0f20', ha='left', va='bottom')
    plt.text(max_lon, min_lat, f"{min_lat:.15f};{max_lon:.15f}",
             fontsize=5, color='#0f0f0f20', ha='right', va='bottom')

    # Sauvegarder l'image
    if transparent_background:
        plt.savefig(output_file, bbox_inches='tight', pad_inches=0, dpi=300, transparent=True)
    else:
        plt.savefig(output_file, bbox_inches='tight', pad_inches=0, dpi=300, facecolor='white')
    plt.close()

    # Ouvrir l'image et l'enregistrer en PNG sans bords blancs
    img = Image.open(output_file)
    img = img.crop(img.getbbox())  # Supprimer les marges blanches
    img.save(output_file)
    
    with open(output_file[0:-3] + "coordsGPS.txt", "w") as txtFile :
        txtFile.write(f"{max_lat:.15f};{min_lon:.15f}\n" + f"{max_lat:.15f};{max_lon:.15f}\n" + f"{min_lat:.15f};{max_lon:.15f}\n" + f"{min_lat:.15f};{min_lon:.15f}")
        

    print(f"Conversion terminée : {output_file}")


def add_gpx_file():
    file_path = filedialog.askopenfilename(title="Sélectionner un fichier GPX", filetypes=[("Fichiers GPX", "*.gpx")])
    if file_path and validate_gpx(file_path):
        color = colorchooser.askcolor(title="Choisir la couleur du tracé")[1]
        if color:
            interval_km = simpledialog.askfloat("Intervalle Kilométrique", "Entrez l'intervalle en km pour les marqueurs :")
            if interval_km and interval_km >= 0.01:
                gpx_files.append(GPXFile(file_path, color, interval_km))
                file_listbox.insert('end', f"{file_path} ({color}, {interval_km} km)")
            else:
                messagebox.showerror("Erreur d'intervalle", "L'intervalle doit être supérieur à 0.01 km.")


def remove_selected_files():
    selected_indices = file_listbox.curselection()
    for index in reversed(selected_indices):
        file_listbox.delete(index)
        del gpx_files[index]


def save_png_file():
    file_path = filedialog.asksaveasfilename(title="Enregistrer sous", defaultextension=".png",
                                             filetypes=[("Fichiers PNG", "*.png")])
    if file_path:
        output_file.set(file_path)


def start_conversion():
    if gpx_files and output_file.get():
        convert_gpx_to_png(gpx_files, output_file.get(), transparent_background.get())
    else:
        messagebox.showwarning("Conversion impossible", "Veuillez ajouter au moins un fichier GPX et choisir un fichier de sortie.")


# Interface graphique avec tkinter
root = Tk()
root.title("Convertisseur GPX en PNG (Multi fichiers avec marqueurs et coordonnées ajustées)")

# Liste des fichiers GPX ajoutés
gpx_files = []

# Variables
output_file = StringVar()
transparent_background = BooleanVar()

# Widgets d'interface
Label(root, text="Fichiers GPX, couleurs et intervalles kilométriques :").pack(pady=5)

# Liste pour afficher les fichiers GPX, leurs couleurs et les intervalles kilométriques
file_listbox = Listbox(root, selectmode=MULTIPLE, width=80, height=10)
file_listbox.pack()

# Boutons pour ajouter et supprimer des fichiers GPX
Button(root, text="Ajouter un fichier GPX", command=add_gpx_file).pack(pady=5)
Button(root, text="Supprimer le(s) fichier(s) sélectionné(s)", command=remove_selected_files).pack(pady=5)

# Sauvegarde du fichier PNG
Label(root, text="Enregistrer sous :").pack(pady=5)
Button(root, text="Choisir l'emplacement du fichier PNG", command=save_png_file).pack()

# Option pour fond transparent
Checkbutton(root, text="Fond transparent", variable=transparent_background).pack(pady=5)

# Bouton de conversion
Button(root, text="Convertir en PNG", command=start_conversion).pack(pady=20)

root.mainloop()

