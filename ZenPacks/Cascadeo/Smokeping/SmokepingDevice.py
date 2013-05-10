from Products.ZenModel.Device import Device


class SmokepingDevice(Device):
    """
    Example device subclass
    """

    _properties = Device._properties

    def __init__(self, id, buildRelations=True):
        super(SmokepingDevice, self).__init__(id, buildRelations)
        super(SmokepingDevice, self).setZenProperty('zSmokepingTarget', self.getZSmokepingTarget())

    def getZSmokepingTarget(self):
        # "World/" might be temporary
        parent_folder = "World/"
        ###device_name = device_name.replace('_', '.')
        device_name = super(SmokepingDevice, self).getDeviceName()
        device_name = device_name.replace('_', '__')
        device_name = device_name.replace('.', '_')

        outfile = open('/home/smokeping_model', 'a')
        outfile.write("Modeling device zSmokepingTarget " + parent_folder + device_name + "\n")
        outfile.close()
        return parent_folder + device_name
####InitializeClass(SmokepingDevice)
