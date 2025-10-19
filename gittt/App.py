from flask import Flask, render_template_string
from models import SQLModel, engine
from auth import auth_bp
from upload import upload_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

app.register_blueprint(auth_bp)
app.register_blueprint(upload_bp)

@app.route('/')
def home():
    return render_template_string('''
        <h1>Welcome to the Log Analyzer App</h1>
        <p><a href="/signup">Sign Up</a></p>
        <p><a href="/signin">Sign In</a></p>
    ''')

SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    app.run(debug=True)
#p