import os
from Airfoil_Generator import Airfoil


def generate_airfoils(t_list, c_list, normalize=True, output_folder="generated_profiles"):
    """
    Genera múltiples perfiles NACA 00xx, los guarda con su .dat
    y devuelve un DICCIONARIO con claves del estilo:
    "NACA0012_c4.5m" : AirfoilObject
    """

    os.makedirs(output_folder, exist_ok=True)
    airfoil_dict = {}

    for t_rel in t_list:
        for c in c_list:

            # Crear objeto Airfoil
            foil = Airfoil.naca00xx(
                t_rel=t_rel,
                c=c,
                normalize=normalize
            )

            # Formato del espesor (ej: 0.12 -> "12")
            thickness_str = f"{int(t_rel * 100):02d}"

            # Crear nombre clave y nombre archivo
            if normalize:
                key = f"NACA00{thickness_str}_c{c:.1f}m_nd"
                filename = f"NACA00{thickness_str}_c{c:.1f}m_nd.dat"
            else:
                key = f"NACA00{thickness_str}_c{c:.1f}m"
                filename = f"NACA00{thickness_str}_c{c:.1f}m.dat"

            filepath = os.path.join(output_folder, filename)

            # Guardar archivo .dat
            foil.save_dat(filepath, non_dim=normalize)

            # Guardar perfil en el diccionario
            airfoil_dict[key] = foil

            print(f"[OK] Generado: {filepath}")

    return airfoil_dict



if __name__ == "__main__":

    espesores = [0.06, 0.08, 0.12, 0.14, 0.16, 0.18, 0.20]  # NACA0006, 08, 12...
    cuerdas   = [1.5, 3.0, 4.5]

    generate_airfoils(espesores, cuerdas, normalize=False)