import hou
import json
import os

"""
from maya side....



    rs_physcical_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'affectsDiffuse',
                               'affectsSpecular',
                               'areaVisibleInRender', 'areaBidirectional', 'volumeRayContributionScale', 'exposure',
                               'areaShape']
    rs_dome_attributes = ['scale', 'rotate', 'translate', 'tex0', 'flipHorizontal','srgbToLinear0'
                        ,'gamma0','exposure0','hue0','saturation0','color', 'affectsSpecular'
                       ,'background_enable', 'volumeRayContributionScale']
    directional_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'affectsDiffuse', 'affectsSpecular',
                  'areaVisibleInRender', 'areaBidirectional', 'volumeRayContributionScale', 'exposure', 'areaShape']
    point_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'decayRate', 'emitDiffuse',
                        'emitSpecular']
    spot_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'coneAngle', 'penumbraAngle', 'dropoff',
                       'decayRate', 'emitDiffuse', 'emitSpecular']


"""

sceneroot = None
use_redshift_lights = False

supported_light_types = ["RedshiftDomeLight",
                         "RedshiftPhysicalLight",
                         # Maya light Types
                         "directionalLight",
                         "pointLight",
                         "spotLight"]


def create_light(name, sceneroot, type):
    """ create lights in the scene"""
    nodeName = name + '_H'
    delete_light = '/obj/{}/{}'.format(sceneroot.name(), name)
    # hou.ui.displayMessage('light to delete {}'.format(delete_light))
    for child in sceneroot.children():
        if child.name() == name:
            child.destroy()

    if type == "RedshiftDomeLight":
        global use_redshift_lights
        if use_redshift_lights:
            light = sceneroot.createNode('rslightdome', '{}'.format(nodeName))
            pass
        else:
            light = sceneroot.createNode('envlight', '{}'.format(nodeName))
    else:
        if use_redshift_lights:
            # make redshift light. It has all we need.
            light = sceneroot.createNode('rslight', '{}'.format(nodeName))
        else:
            # make mantra light.
            light = sceneroot.createNode('hlight', '{}'.format(nodeName))

    return light


def filepath():
    """ ask for file path"""
    filepath = hou.ui.selectFile()
    return filepath


def read_json():
    """ let user select the attribute filepath to read  """
    path = filepath()
    if path.lower().endswith('.json'):
        read_file = open('{}'.format(path), 'r')
        lampattr = json.load(read_file)
        return lampattr, path
    else:
        hou.ui.displayMessage('Please select a .json file ')


def import_fbx(path):
    """ imports the fbx from each lamp """
    newpath = os.path.dirname(path) + '/'
    os.chdir(newpath)

    fname = str(path).split('/')[-1:][0]
    fname = str(fname).replace('.json', '.fbx')
    hou.hipFile.importFBX(fname)
    fname = fname.replace(".", "_")
    global sceneroot
    sceneroot = hou.node('/obj/{}/'.format(fname))
    # fbxpath = '{}/'.format(path) + fname
    # hou.hipFile.importFBX('scene.fbx')


def translate_light():
    """ position the light with correct scale,rotation and translation """
    lampattr, path = read_json()
    # import fbx
    import_fbx(path)

    globalnull = sceneroot.createNode('null', 'size_locator')
    globalnull.setParms({'scale': 1})

    for lamp in lampattr:
        name = lamp.get('name')
        type = lamp.get('type')
        if type not in supported_light_types:
            # unsupported light type found. Don't bother. This "should" be fixed in maya side.
            continue

        light = create_light(name, sceneroot, type)
        # Connect lights to Null objects
        # null = hou.node('/obj/scene_fbx/{}/'.format(name))
        light.setInput(0, globalnull, 0)
        # null.setInput(0, globalnull, 0)
        scales = lamp.get('scale')
        colors = lamp.get('color')
        global use_redshift_lights

        if type.startswith("Redshift"):
            # a redshift light Duh
            if type == "RedshiftDomeLight":
                set_attributes_redshift_light(type, light, lamp)
                pass
            if type == "RedshiftPhysicalLight":
                light.setParms({'light_type': 3})
                for scale in scales:
                    light.setParms({'areasize1': (scale[0] * 2), 'areasize2': (scale[1] * 2)})
                set_attributes_redshift_light(type, light, lamp)

        elif type == 'directionalLight':
            if use_redshift_lights:
                light.setParms({'light_type': 0})
                set_attributes_redshift_light(type, light, lamp)
            else:
                light.setParms({'light_type': 7})
                set_attributes_maya_light(type, light, lamp)

        elif type == 'spotLight':
            if use_redshift_lights:
                light.setParms({'light_type': 2})
                set_attributes_redshift_light(type, light, lamp)
            else:
                light.setParms({'light_type': 0})
                light.setParms({'coneenable': True})
                set_attributes_maya_light(type, light, lamp)

        elif type == 'pointLight':
            if use_redshift_lights:
                light.setParms({'light_type': 1})
                set_attributes_redshift_light(type, light, lamp)

            else:
                light.setParms({'light_type': 0})
                set_attributes_maya_light(type, light, lamp)

        for color in colors:
            light.setParms({'light_colorr': color[0], 'light_colorg': color[1], 'light_colorb': color[2]})
        comment = lamp.get('filename')
        positions = lamp.get('translate')
        for pos in positions:
            light.setParms({'tx': pos[0], 'ty': pos[1], 'tz': pos[2]})
        rotations = lamp.get('rotate')
        for rot in positions:
            light.setParms({'rx': rot[0], 'ry': rot[1], 'rz': rot[2]})

    light.setGenericFlag(hou.nodeFlag.DisplayComment, True)
    light.setComment(comment)


    sceneroot.layoutChildren()


def set_attributes_redshift_light(type, light, lamp):
    """ set the attributes for the light """
    global use_redshift_lights
    if use_redshift_lights:
        if type == "RedshiftDomeLight":
            light.setParms({'env_map': lamp.get('tex0')})
            light.setParms({'RSL_flipHorizontal': lamp.get('flipHorizontal')})

            if lamp.get('srgbToLinear0'):
                light.setParms({'tex0_gammaoverride': True})
                light.setParms({'tex0_srgb': True})
            if lamp.get('gamma0') != 1:
                light.setParms({'tex0_gammaoverride': True})
                light.setParms({'tex0_gamma': lamp.get('gamma0')})
            light.setParms({'RSL_exposure': lamp.get('exposure0')})
            light.setParms({'RSL_hue': lamp.get('hue0')})
            light.setParms({'RSL_saturation': lamp.get('saturation0')})
            light.setParms({'background_enable': lamp.get('background_enable')})
            light.setParms({'RSL_affectDiffuse': lamp.get('affectsDiffuse')})
            light.setParms({'RSL_affectSpecular': lamp.get('affectsSpecular')})
            light.setParms({'RSL_volumeScale': lamp.get('volumeRayContributionScale')})
        if type == "RedshiftPhysicalLight":
            light.setParms({'RSL_intensityMultiplier': lamp.get('intensity')})
            light.setParms({'Light1_exposure': lamp.get('exposure')})
            light.setParms({'RSL_affectDiffuse': lamp.get('affectsDiffuse')})
            light.setParms({'RSL_affectSpecular': lamp.get('affectsSpecular')})
            light.setParms({'RSL_bidirectional': lamp.get('areaBidirectional')})
            light.setParms({'RSL_visible': lamp.get('areaVisibleInRender')})
            light.setParms({'RSL_volumeScale': lamp.get('volumeRayContributionScale')})
            light.setParms({'RSL_areaShape': lamp.get('areaShape')})
        else:
            light.setParms({'RSL_affectDiffuse': lamp.get('emitDiffuse')})
            light.setParms({'RSL_affectSpecular': lamp.get('emitSpecular')})
            light.setParms({'RSL_volumeScale': lamp.get('volumeRayContributionScale')})

    else:
        light.setParms({'light_intensity': lamp.get('intensity')})
        light.setParms({'light_exposure': lamp.get('exposure')})

        if type == "RedshiftDomeLight":
            light.setParms({'env_map': lamp.get('tex0')})
            light.setParms({'light_contribprimary': lamp.get('background_enable')})

        if type == "RedshiftPhysicalLight":
            light.setParms({'light_contribprimary': lamp.get('areaVisibleInRender')})

    # create comment-description for each light


def set_attributes_maya_light(type, light, lamp):
    light.setParms({'light_intensity': lamp.get('intensity')})
    light.setParms({'light_exposure': lamp.get('exposure')})
    diffuse = lamp.get('emitDiffuse');
    spec = lamp.get('emitSpecular');
    if not diffuse:
        pass
    if not spec:
        pass
    if type == "directionalLight":
        # directional only attributes
        pass
    if type == "pointLight":
        # pointlight only attributes
        pass
    if type == "spotLight":
        # spotlight only attributes
        light.setParms({'coneangle': lamp.get('coneAngle')})
        light.setParms({'conedelta': lamp.get('penumbraAngle')})
        light.setParms({'coneroll': lamp.get('dropoff')})
        pass
    if type == "spotLight" or type == "pointLight":

        # both spot and point stuff.
        decay = lamp.get("decayRate")
        if decay == 0:
            light.setParms({'atten_type': 0})
        elif decay == 1:
            light.setParms({'atten_type': 2})
        elif decay == 2:
            light.setParms({'atten_type': 2})
        elif decay == 3:
            light.setParms({'atten_type': 2})


def main(**kwargs):
    translate_light()
    hou.ui.displayMessage('Lights have been generated!')


# if __name__ == "__main__":
#    translate_light()
#    hou.ui.displayMessage('Lights have been generated!')


main(**kwargs)