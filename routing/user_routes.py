import enum

class UserRoutes(enum.Enum):
    Empty = enum.auto()
    MainMenu = enum.auto()
    RoomMenu = enum.auto()
    RoomSettings = enum.auto()
    QueueView = enum.auto()
    QueueSettings = enum.auto()
    Profile = enum.auto()
    RoomUsersList = enum.auto()
    MakeAnnouncement = enum.auto()
    AssignmentMenu = enum.auto()