import maya.cmds as cmds
import json
import os
import maya.mel as mel


def list_all_lamps():
    lamps = cmds.ls(selection=True)
    if not lamps:
        cmds.confirmDialog(title='Confirm', message='Please select any Light')
    else:
        return lamps


def attribute_generator(lamps):
    lamp_dict = []

    supported_light_types = ["RedshiftDomeLight",
                   "RedshiftPhysicalLight",
                   # Maya light Types
                   "directionalLight",
                   "pointLight",
                   "spotLight"]

    light_types = ["RedshiftDomeLight",
                   "RedshiftIESLight",
                   "RedshiftPhysicalLight",
                   "RedshiftPortalLight",
                   # Maya light Types
                   "directionalLight",
                   "pointLight",
                   "spotLight"]

    rs_physcical_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'affectsDiffuse',
                               'affectsSpecular',"lightType",
                               'areaVisibleInRender', 'areaBidirectional', 'volumeRayContributionScale', 'exposure',
                               'areaShape']
    rs_dome_attributes = ['scale', 'rotate', 'translate', 'tex0', 'flipHorizontal','srgbToLinear0'
                        ,'gamma0','exposure0','hue0','saturation0','color', 'affectsDiffuse','affectsSpecular'
                       ,'background_enable', 'volumeRayContributionScale']
    directional_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'emitDiffuse','emitSpecular']
    point_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'decayRate', 'emitDiffuse',
                        'emitSpecular']
    spot_attributes = ['scale', 'rotate', 'translate', 'intensity', 'color', 'coneAngle', 'penumbraAngle', 'dropoff',
                       'decayRate', 'emitDiffuse', 'emitSpecular']


    for lamp in lamps:
        no_light = False

        shapes = cmds.listRelatives(lamp, s=True)
        light_type = cmds.objectType(shapes[0])

        if light_type not in supported_light_types:
            no_light = True
            #cmds.confirmDialog(title='LIGHT not supported', message='Could not add {}. Is it a light?'.format(lamp))
            cmds.confirmDialog(title='This light is not supported', message='Light type is {} is not supported. Aborting.'.format(light_type))
            return False;
            lamps.remove(lamp)
            continue
        else:
            lamp_entry = dict()
            if light_type == "RedshiftDomeLight":
                lamp_entry = {attr: cmds.getAttr('{}.{}'.format(lamp, attr)) for attr in rs_dome_attributes};
                lamp_entry['type'] = 'RedshiftDomeLight'
            elif light_type == "RedshiftPhysicalLight":
                lamp_entry = {attr: cmds.getAttr('{}.{}'.format(lamp, attr)) for attr in rs_physcical_attributes};
                lamp_entry['type'] = 'RedshiftPhysicalLight'
            elif light_type == "directionalLight":
                lamp_entry = {attr: cmds.getAttr('{}.{}'.format(lamp, attr)) for attr in directional_attributes};
                lamp_entry['type'] = 'directionalLight'
            elif light_type == "pointLight":
                lamp_entry = {attr: cmds.getAttr('{}.{}'.format(lamp, attr)) for attr in point_attributes};
                lamp_entry['type'] = 'pointLight'
            elif light_type == "spotLight":
                lamp_entry = {attr: cmds.getAttr('{}.{}'.format(lamp, attr)) for attr in spot_attributes};
                lamp_entry['type'] = 'spotLight'
            lamp_dict.append(lamp_entry)

    #try:
    #    lamp_dict = [{attr: cmds.getAttr('{}.{}'.format(lamp, attr)) for attr in attributes} for lamp in lamps]
    #except ValueError:
    #    lamp_dict = [{attr: cmds.getAttr('{}.{}'.format(lamp, attr)) for attr in point_attributes} for lamp in lamps]
    filepath = cmds.file(q=True, sn=True)
    filename = os.path.basename(filepath)
    raw_name, extension = os.path.splitext(filename)
    for dicts, name in zip(lamp_dict, lamps):
        dicts['name'] = name
        dicts['filename'] = raw_name
    return lamp_dict


def ask_filepath_location():
    basicFilter = "*.json"
    filepath = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2)
    return filepath


def write_attributes(*args):
    """ Write out the attributes in json and fbx"""
    attrdict = write_json()
    if not attrdict:
        return False;
    filename = ''.join(ask_filepath_location())
    file = open('{}'.format(filename), 'w')
    file.write(attrdict)
    file.close()
    write_fbx(filename)
    cmds.confirmDialog(title='LightExporter', message='Lights have been exported')


def write_fbx(filename):
    path = os.path.dirname(filename)
    fname = str(filename).split('/')[-1:][0]
    fname = str(fname).replace('.json','.fbx')
    fbxpath = '{}/'.format(path) + fname
    mel.eval('FBXExportBakeComplexAnimation -q; ')  # bake animation
    mel.eval('FBXExport -f "{}" -s'.format(fbxpath))  # remove -s to export all


def world_duplicater(*arg):
    """ bake lamps to world space and remove from parent"""
    lamps = cmds.ls(selection=True)
    bakelist = []
    for lamp in lamps:
        par = cmds.listRelatives(lamp, parent=True)
        if not par:
            continue
        else:
            duplicated_lamps = cmds.duplicate(lamp, name=lamp + '_bakedToWorld', rc=True, rr=True)
            children = cmds.listRelatives(duplicated_lamps, c=True, pa=True)[1:]
            for child in children:
                cmds.delete(child)
            tobake = cmds.parent(duplicated_lamps, w=True)
            bakelist.append(tobake)
            cmds.parentConstraint(lamp, tobake, mo=False)
            cmds.scaleConstraint(lamp, tobake, mo=False)

        # get Start and End Frame of Time Slider
    startframe = cmds.playbackOptions(q=True, minTime=True)
    endframe = cmds.playbackOptions(q=True, maxTime=True)
    for i in bakelist:
        cmds.bakeResults(i, t=(startframe, endframe))
        cmds.delete(i[0] + '*Constraint*')
    cmds.confirmDialog(title='Duplicater', message='Baked and duplicated child lights to worldscale')


def write_json():
    attribs = attribute_generator(list_all_lamps())
    if attribs:
        attr = json.dumps(attribs)
        return attr
    else:
        return False;



def launch_interface():
    """ menu to start function with buttons"""
    cmds.window(width=250, title='Light Exporter')
    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label='Step1. Bake and duplicate selected lights', command=world_duplicater)
    cmds.button(label='Step2. Export selected lights', command=write_attributes)
    cmds.showWindow()


if __name__ == '__main__':
    launch_interface()
