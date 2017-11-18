from .ar import AutoRooms
from .tmpc import TempChannels
from .roomtools import RoomTools
import sys


def setup(bot):
    if sys.version_info >= (3, 6, 2):
        global roomtoolscmdgroup
        bot.add_cog(RoomTools(bot))
        roomtoolscmdgroup = bot.get_cog('RoomTools').roomtoolsgroup
        if True:  # bot.get_cog('RoomTools').ar_active:
            bot.add_cog(AutoRooms(bot))
        if False:  # bot.get_cog('RoomTools').tmpc_active:
            bot.add_cog(TempChannels(bot))
    else:
        raise RuntimeError("This package requires python version >= 3.6.2")
