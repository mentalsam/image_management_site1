from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from PIL import Image as PILImage
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)  # アップロード日時を追加

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    images = Image.query.all()
    return render_template('index.html', images=images)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # サムネイルを作成
        img = PILImage.open(filepath)
        img.thumbnail((200, 200))
        thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumb_' + filename)
        img.save(thumbnail_path)

        new_image = Image(filename=filename)
        db.session.add(new_image)
        db.session.commit()

        return redirect(url_for('index'))

    return redirect(request.url)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_image(id):
    image = Image.query.get_or_404(id)  # 画像を取得（存在しない場合は404エラー）
    
    # ファイルを削除
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumb_' + image.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
    
    # データベースからレコードを削除
    db.session.delete(image)
    db.session.commit()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():  # アプリケーションコンテキスト内で実行
        db.create_all()  # データベースの初期化
    app.run(debug=True)