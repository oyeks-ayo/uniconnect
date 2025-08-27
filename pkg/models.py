from datetime import datetime
from flask_sqlalchemy import SQLAlchemy # type: ignore

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    admin_pwd = db.Column(db.String(200), nullable=False)
    datereg_signup = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SignUp {self.username}>"


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    user_pwd = db.Column(db.String(200), nullable=False)
    matricNo = db.Column(db.String(200), nullable=False, unique=True)
    datereg_signup = db.Column(db.DateTime, default=datetime.utcnow)

    # RELATIONSHIPS
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    posts = db.relationship('Posts', backref='user', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Likes', backref='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SignUp {self.username}>"
    
class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dept_name = db.Column(db.String(190), nullable=False, unique=True)
    dept_code = db.Column(db.String(20), nullable=False, unique=True)
    faculty = db.Column(db.String(100), nullable=False)
    est_year = db.Column(db.String(4), nullable=False)
    hod = db.Column(db.String(100), nullable=False)

    # Relationship: one department can have many profiles
    profiles = db.relationship('Profile', backref='department', lazy=True, cascade="all, delete-orphan")

    # def __repr__(self):
    #     return f"<Department id={self.id}>"
    def __repr__(self):
    # Use __dict__.get so it won’t trigger a lazy load
        id_val = self.__dict__.get("id", None)
        name_val = self.__dict__.get("dept_name", None)
        return f"<Department id={id_val} name={name_val}>"


    
class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    pix = db.Column(db.String(500))
    faculty = db.Column(db.String(100))
    dept_id = db.Column(db.Integer, db.ForeignKey('department.id', ondelete='CASCADE'), nullable=False)
    level = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    bio = db.Column(db.Text)
    interest = db.Column(db.String(500))

    def __repr__(self):
        id_val = self.__dict__.get("id", None)
        user_val = self.__dict__.get("user_id", None)
        return f"<Profile id={id_val} user={user_val}>"

    # def __repr__(self):
    #     return f'<Profile {self.id}>'
    
class Posts(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text)
    image = db.Column(db.String(100))
    video = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: one post can have many likes
    likes = db.relationship("Likes", backref="post", lazy=True, cascade="all, delete-orphan")
    

class Likes(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
    )

    def __repr__(self):
        return f"<Like User={self.user_id} Post={self.post_id}>"


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    user = db.relationship('Users', backref='comments', lazy=True)
    post = db.relationship('Posts', backref='comments', lazy=True)

    def __repr__(self):
        return f"<Comment {self.text[:20]}... by User {self.user_id} on Post {self.post_id}>"
    
class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Announcement {self.title}>"