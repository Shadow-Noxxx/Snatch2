class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = 7819315360
    sudo_users = "7819315360" , "8162803790"
    GROUP_ID = "-1002620872464"
    TOKEN = "7252339580:AAFFkJRdl32Xhoiitj9WUsS5wI590mpcoVc"
    mongo_url = "mongodb+srv://TEAMBABY01:UTTAMRATHORE09@cluster0.vmjl9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    PHOTO_URL = ["https://telegra.ph/file/b925c3985f0f325e62e17.jpg", "https://telegra.ph/file/4211fb191383d895dab9d.jpg"]
    SUPPORT_CHAT = "FOS_CHATTING_GROUP"
    UPDATE_CHAT = "FOS_BOTS"
    BOT_USERNAME = "Yoruichi_ProBot"
    api_id = 23212132
    api_hash = "1c17efa86bdef8f806ed70e81b473c20"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
