import logging


class snap(object):
    ''' class ARRAY - a storage device which we creates snaps, LUNS, and filesystems
    '''

    def __init__(self, array, name="", id=""):
        '''
        :param name: simple snap shot object
        :param id:
        array - object of type array
        name - name of snapshot
        id - id that the array calls this snapshot (string representation of long integer)
        :return:
        '''
        self.snapName = ""
        self.snapID = ""
        self.array = type(array)
        if name:
            self.snapName = name
        if id:
            self.snapID = id

    def delete(self):
        ## This is broken -- how do I get the array object so
        ## I don't need to recreate this code?
        ##
        logging.debug('delete({})'.format(self))
        if len(self.snapID) > 0 or len(self.snapName) > 0:
            self.array.deleteSnap(self.array, snapName=self.snapName, snapID=self.snapID)
        else:
            logging.critical("can't delete snap - object has no ID or name")
            
    def __str__(self):
        ''' print snap name and id
        :return:
        '''
        _s = 'snapName: {} snapID: {}'.format(self.snapName, self.snapID)
        return _s

    def getID(self):
        """
        getID
        :return: id
        """
        return self.snapID

    def getName(self):
        """
        getName
        :return: name
        """
        return self.snapName

    def setName(self, name):
        """

        :param name:
        :return:
        """
        self.SnapName = name

    def setID(self, id):
        """

        :param id:
        :return:
        """
        self.SnapID = id
