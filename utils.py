import matplotlib.pyplot as plt
import numpy as np


def show_wells(well_name, wells):
    if well_name == 'ISYNTH':
        nx, ny = 6, 8
        bg_color = '#B4DCA0'
    elif well_name == 'RACKL':
        nx, ny = 5, 16
        bg_color = '#AA96D5'
    elif well_name == 'RACKR':
        nx, ny = 3, 10
        bg_color = '#AA96D5'

    text_props = dict(fontsize=15, color='r', fontweight='bold', ha='center', va='center')
    fig, ax = plt.subplots(1, 1, figsize=(8*(nx+1)/(ny+1), 8), tight_layout=True)
    for i_x in range(nx):
        for i_y in range(ny):
            xy = (i_x+1, ny-i_y)
            idx = i_x*ny+i_y+1
            if idx in wells:
                ax.add_patch(plt.Circle(xy, radius=0.35, fc='#FFFF6F'))
                ax.text(xy[0], xy[1], str(idx), **text_props)
            else:
                ax.add_patch(plt.Circle(xy, radius=0.35, fc='#3A6EA5'))

    fig.patch.set_facecolor(bg_color)
    ax.set_aspect('equal')
    ax.set_xlim(0, nx+1)
    ax.set_ylim(0, ny+1)
    ax.set_axis_off()
    plt.show()

def well_selector(well_name, wells=[]):
    if well_name == 'ISYNTH':
        nx, ny = 6, 8
        bg_color = '#B4DCA0'
    elif well_name == 'RACKL':
        nx, ny = 5, 16
        bg_color = '#AA96D5'
    elif well_name == 'RACKR':
        nx, ny = 3, 10
        bg_color = '#AA96D5'

    fontsize = int(30*(nx+1)/(ny+1))
    text_props = dict(fontsize=fontsize, color='k', fontweight='bold', ha='center', va='center')
    fig, ax = plt.subplots(1, 1, figsize=(8*(nx+1)/(ny+1), 8), tight_layout=True)

    # creating clickable circle
    circles = []
    def create_circle(xy, highlight):
        txt_obj = ax.text(xy[0], xy[1], str(idx), **text_props)
        def create_click(text_obj):
            def click(c, e):
                if c.contains(e)[0]:
                    if c.get_linestyle() == 'solid':
                        c.set_facecolor('#FFFF6F')
                        c.set_linestyle('dashed')
                        text_obj.set_color('r')
                    else:
                        c.set_facecolor('#3A6EA5')
                        c.set_linestyle('solid')
                        text_obj.set_color('k')
                    fig.canvas.draw()
                    return True, {}
                else:
                    return False, {}
            return click

        cir_obj = plt.Circle(xy, radius=0.35, picker=create_click(txt_obj))
        circles.append(cir_obj)
        if highlight:
            cir_obj.set_facecolor('#FFFF6F')
            cir_obj.set_linestyle('dashed')
            txt_obj.set_color('r')
        ax.add_patch(cir_obj)

    for i_x in range(nx):
        for i_y in range(ny):
            xy = (i_x+1, ny-i_y)
            idx = i_x*ny+i_y+1
            if idx in wells:
                create_circle(xy, True)
            else:
                create_circle(xy, False)

    fig.patch.set_facecolor(bg_color)
    ax.set_aspect('equal')
    ax.set_xlim(0, nx+1)
    ax.set_ylim(0, ny+1)
    ax.set_axis_off()
    plt.show()

    selected_wells = []
    for i, c in enumerate(circles):
        if c.get_linestyle()=='dashed':
            selected_wells.append(i+1)
    print(selected_wells)


if __name__ == '__main__':
    # show_wells('RACKL', [1, 5, 80])
    well_selector('ISYNTH', [1, 5, 10])


