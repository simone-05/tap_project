from app import app
# from flask_failsafe import failsafe

# @failsafe
# def create_app():
#     # Per non stoppare il serving di flask, a causa di errori di sintassi
# #   note that the import is *inside* this function so that we can catch
# #   errors that happen at import time
#   from app import app
#   return app

# if __name__ == "__main__":
# create_app().run(debug=False, host="0.0.0.0", port=5001)
app.run(debug=False, host="0.0.0.0", port=5001)
