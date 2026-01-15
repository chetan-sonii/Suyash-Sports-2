import os
import secrets
from flask import current_app
# from flask_mail import Message
from flask import url_for


def save_avatar(form_picture):
    # 1. Generate a random name to prevent filename collisions
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext

    # 2. Construct the full path
    # Make sure this folder exists: app/static/images/uploads/avatars
    picture_path = os.path.join(current_app.root_path, 'static/images/uploads/avatars', picture_fn)

    # 3. Save the image
    form_picture.save(picture_path)

    return picture_fn





def send_reset_email(user):
    token = user.get_reset_token()
    # msg = Message('Password Reset Request',
    #               sender='noreply@sportsmanager.com',
    #               recipients=[user.email])

    link = url_for('auth.reset_token', token=token, _external=True)

#     print(f'''To reset your password, visit the following link: {link}
# If you did not make this request then simply ignore this email.
# ''')
    print(f'''To reset your password, visit the following link: {link}
     If you did not make this request then simply ignore this email.
     ''')
    # mail.send(msg)