class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = 6138142369
    sudo_users = 7819315360
    GROUP_ID = "-1002003248653"
    TOKEN = "7429550304:AAEFhObQ2DsKF8H9di9bVkPb_dZIZufnLy8"
    mongo_url = "mongodb+srv://TEAMBABY01:UTTAMRATHORE09@cluster0.vmjl9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    PHOTO_URL = ["https://telegra.ph/file/b925c3985f0f325e62e17.jpg", "https://telegra.ph/file/4211fb191383d895dab9d.jpg"]
    SUPPORT_CHAT = "MidexozSupport"
    UPDATE_CHAT = "MidexozBotUpdates"
    BOT_USERNAME = "Sylusgrace_Bot"
    CHARA_CHANNEL_ID = "-1002685904693"
    api_id = 29348525
    api_hash = "d815eb5b92d9ba6e35c45fa4a85db492"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
