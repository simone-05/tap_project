from flask import Flask

app = Flask(__name__)

from app import views
from app import producer


# if __name__ == '__main__':
# app.run(debug=True, host='0.0.0.0')
