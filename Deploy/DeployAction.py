#
# (c) Peralta Informatics 2007
# $Id: DeployAction.py 44 2007-12-11 05:05:14Z andrei $
#

class Action(object):
    
    Empty               = 0x0
    Help                = 0x1
    DeployDatabase      = 0x2
    SkipDatabase        = 0x4
    DeleteDatabase      = 0x8
    UpdateWebConfig     = 0x10
    DeleteWebsite       = 0x20
    CreateWebsite       = 0x40
    BuildReleaseBundle  = 0x80
    Info                = 0x100
    PushFiles           = 0x200

