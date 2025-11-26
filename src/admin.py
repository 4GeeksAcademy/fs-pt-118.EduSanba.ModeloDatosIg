import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import db, User, Profile, Post, Comment, Followers

# Oculta password en el admin
class UserAdmin(ModelView):
    column_exclude_list = ["password"]
    form_columns = ["email", "password", "nickname", "is_active"]

  # antes de borrar un usuario, elimina lo que lo referencia
    def on_model_delete(self, model):

        # followers donde aparece como seguidor o seguido
        db.session.query(Followers).filter(
            (Followers.follower_id == model.id) | (Followers.followed_id == model.id)
        ).delete(synchronize_session=False)

        # su perfil 1-1 si existe
        db.session.query(Profile).filter_by(user_id=model.id).delete(synchronize_session=False)

        # comentarios escritos por el usuario
        db.session.query(Comment).filter_by(user_id=model.id).delete(synchronize_session=False)

        #  posts y por el FK caen tambien sus comments del post)
        db.session.query(Post).filter_by(user_id=model.id).delete(synchronize_session=False)

# post para elegir el autor
class PostAdmin(ModelView):
    column_list  = ["id", "author", "image_url", "caption", "created_at"]
    form_columns = ["author", "image_url", "caption"]
    column_labels = {"author": "User"}

# comment para elegir post y autor
class CommentAdmin(ModelView):
    column_list  = ["id", "post", "author", "content", "created_at"]
    form_columns = ["post", "author", "content"]

# Profile àra elegir user sera el dueño
class ProfileAdmin(ModelView):
    column_list  = ["id", "user", "bio", "created_at"]
    form_columns = ["user", "bio"]

# Followers
class FollowersAdmin(ModelView):
    column_list  = ["id", "follower", "followed", "created_at"]
    form_columns = ["follower", "followed"]

   

    form_widget_args = {
        "follower": {"required": True},
        "followed": {"required": True},
    }

    action_disallowed_list = ['delete']
    def on_model_change(self, form, model, is_created):
        follower = getattr(form, "follower", None)
        followed = getattr(form, "followed", None)
        follower_obj = follower.data if follower else None
        followed_obj = followed.data if followed else None

        if follower_obj is None or followed_obj is None:
            raise ValueError("Debes seleccionar 'Seguidor' y 'Seguido'.")

        if follower_obj.id == followed_obj.id:
            raise ValueError("No puedes seguirte a ti mismo.")
        
        model.follower = follower_obj
        model.followed = followed_obj
def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    admin.add_view(UserAdmin(User, db.session))           # User
    admin.add_view(ProfileAdmin(Profile, db.session))     # Profile
    admin.add_view(PostAdmin(Post, db.session))           # Post
    admin.add_view(CommentAdmin(Comment, db.session))     # Comment
    admin.add_view(FollowersAdmin(Followers, db.session)) # Follower