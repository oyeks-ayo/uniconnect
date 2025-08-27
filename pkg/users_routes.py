from datetime import datetime
from functools import wraps
import json,os, secrets
from sqlalchemy import func, or_ # type: ignore
from flask import render_template,request,redirect,url_for,flash,make_response,session,jsonify
from flask_wtf.csrf import CSRFError, generate_csrf # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash
from pkg import app,csrf
from pkg.models import db, Users,Profile,Posts,Likes, Comment,Department,Announcement

@app.context_processor
def inject_users():
# **************FOR CSRF TOKEN AND SERACH BOX****************
    vc_id = Users.query.filter_by(id=session.get('vconline')).first() if session.get('vconline') else None
    return dict(csrf_token=generate_csrf, vc_id=vc_id)
# **************FOR CSRF TOKEN AND SERACH BOX****************

# ****************** TO PREVENT USERS FROM USING BACK BUTTON TO RETURN TO PLATFORM AFTER LOGIN **************************
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache,no-store,must-revalidate'
    return response
# ****************** TO PREVENT USERS FROM USING BACK BUTTON TO RETURN TO PLATFORM AFTER LOGIN **************************

# *********************************** LOGIN DECORATOR **************************************************
def login_required(f):
    @wraps(f)
    def login_decorator(*args, **kwargs):
        if session.get('isonline') != None:
            return f(*args,**kwargs)
        else:
            flash('You need to be logged in before you can visit page', category='error')
            return redirect(url_for('user_login'))
    return login_decorator
# *********************************** LOGIN DECORATOR **************************************************

# *********************************** TIME FUNCTION **************************************************
@app.template_filter('time_ago')
def time_ago_filter(dt):
    now = datetime.utcnow()
    diff = now - dt
    
    periods = [
        ('year', 365*24*60*60),
        ('month', 30*24*60*60),
        ('day', 24*60*60),
        ('hour', 60*60),
        ('minute', 60)
    ]
    
    for period, seconds in periods:
        value = diff.total_seconds() // seconds
        if value:
            return f"{int(value)} {period}{'s' if value > 1 else ''} ago"
    return "just now"

# <small>Posted {{ project.datereg_project|time_ago }}</small>
# {Example output: "3 hours ago" #}
# *********************************** TIME FUNCTION **************************************************

# *********************************** ERROR HANDLER **************************************************
@app.errorhandler(400)
def bad_request(e):
    # Log the error details 
    app.logger.error(f"403 Error: {str(e)}", exc_info=True)
    # Return a custom 400 error page
    return render_template('user/errorpage.html', error400=e), 400

@app.errorhandler(403)
def forbidden(e):
    # Log the error details
    app.logger.error(f"403 Error: {str(e)}", exc_info=True)
    # Return a custom 403 error page
    return render_template('user/errorpage.html', error403=e), 403

@app.errorhandler(404)
def page_not_found(e):
    # Log the error details
    app.logger.error(f"404 Error: {str(e)}", exc_info=True)
    # Return a custom 404 error page
    return render_template('user/errorpage.html', error404=e), 404

@app.errorhandler(405)
def forbidden(e):
    # Log the error details
    app.logger.error(f"405 Error: {str(e)}", exc_info=True)
    # Return a custom 405 error page
    return render_template('user/errorpage.html', error405=e), 405

@app.errorhandler(500)
def internal_server_error(e):
    # Log the error details
    app.logger.error(f"500 Error: {str(e)}", exc_info=True)
    # Return a custom 500 error page
    return render_template('user/errorpage.html', error500=e), 500

# *********************************** ERROR HANDLER **************************************************

# *********************************** HOME ROUTE **************************************************

@app.route('/', methods=['GET','POST'])
@login_required
def home():

    user_id = session['isonline']
    posts = db.session.query(Posts).order_by(Posts.date.desc()).all()
    profile = Profile.query.filter_by(user_id=user_id).first()

    # Dictionary of liked posts for this user
    liked_posts = {}
    if user_id:
        user_likes = Likes.query.filter_by(user_id=user_id).all()
        liked_posts = {like.post_id: True for like in user_likes}

    if request.method == 'POST':
        try:
            content = request.form.get('content')
            image = request.files.get('image')
            video = request.files.get('video')

            if image and image.filename:
                format = ['.jpg', '.png', '.jpeg', '.webp']
                img_name = image.filename
                _, ext = os.path.splitext(img_name)
                if ext.lower() in format:
                    img_name = secrets.token_hex(10) + ext
                    image.save('pkg/static/uploads/image/'+img_name)

            if video and video.filename:
                format = ['.mp4', '.mov', '.webm']
                vid_name = video.filename
                _, ext = os.path.splitext(vid_name)
                if ext.lower() in format:
                    vid_name = secrets.token_hex(10) + ext
                    video.save('pkg/static/uploads/videos/'+vid_name)

            post = Posts(content=content,
                         image=img_name,
                         video=vid_name,
                         user_id=user_id)

            db.session.add(post)
            db.session.commit()

            flash('Post sent', category='success')
            return redirect(url_for('home'))
            

        except ValueError as e:
            app.logger.error(f"Message: {str(e)}", exc_info=True)
            flash(f'{str(e)}', category='error')
        except Exception as e:
            app.logger.error(f"Error during user signup: {str(e)}", exc_info=True)
            flash(f'An error occured during upload try again later {str(e)}', category='error')
    return render_template('user/home.html',posts=posts,
                                            liked_posts=liked_posts,
                                            user_id=user_id,
                                            profile=profile)

# *********************************** HOME ROUTE **************************************************


# *********************************** USER SIGNUP **************************************************
@app.route('/user/signup/', methods=['GET','POST'])
def user_signup():
    try:
        dept = Department.query.all()

        if request.method == 'POST':
            fname = request.form.get('fname','').strip()
            lname = request.form.get('lname','').strip()
            uname = request.form.get('uname','').strip()
            email = request.form.get('email','').strip()
            pwd1 = request.form.get('pwd1','').strip()
            pwd2 = request.form.get('pwd2','').strip()
            matricNo = request.form.get('matric_no','').strip()

            if not fname or not lname or not uname or not email or not pwd1 or not pwd2 or not matricNo:
                raise ValueError('Input field cannot be empty')
            if pwd1 != pwd2:
                raise ValueError('Passwords do not match!')
            # if len(pwd1) < 8:
                # raise ValueError('Password must be at least 8 characters long!') #
            # Validate email format
            if '@' not in email or '.' not in email.split('@')[-1]:
                raise ValueError('Invalid email format!')
            else:
                # Check if username or email already exists
                existing_user = Users.query.filter(
                    (Users.username == uname) | (Users.email == email)
                ).first()
                
                if existing_user:
                    raise ValueError('Username or Email already exists!')
                
                # Check if matricNo already exists
                existing_matric = Users.query.filter_by(matricNo=matricNo).first()
                if existing_matric:
                    raise ValueError('Matriculation Number already exists!')

                # Create new user
                pwd1 = generate_password_hash(pwd1)
                fname = fname.upper()
                lname = lname.upper()
                uname = uname.lower()
                email = email.lower()
                # Ensure matricNo is stored as a string (if needed)
                matricNo = str(matricNo).strip().upper()

                # Create user instance
                
                user = Users(   fname=fname,
                                lname=lname,
                                username=uname,
                                email=email,
                                user_pwd=pwd1,
                                matricNo=matricNo)
                db.session.add(user)
                db.session.commit()
                flash('You have successfully signed up', category='success')
                return render_template('user/aftersignup.html')
    except ValueError as ve:
        flash(str(ve), category='error')
    except Exception as e:
        app.logger.error(f"Error during user signup: {str(e)}", exc_info=True)
        flash(f'An error occurred while signing up. Please try again later.', category='error')
    return render_template('user/signup.html', dept=dept)
# *********************************** USER SIGNUP **************************************************

# *********************************** USER LOGIN **************************************************
@app.route('/user/login/', methods=['GET','POST'])
def user_login():

    if request.method == 'POST':
        try:
            uname = request.form.get('uname','').strip()
            pwd = request.form.get('pwd','').strip()

            if not uname or not pwd:
                raise ValueError('Input fields cannot be empty')
            # Check if user exists
            user = Users.query.filter((Users.username == uname) | (Users.email == uname)).first()
            # user = Users.query.filter(or_(Users.username==uname,Users.email==uname)).first()
            if not user:
                raise ValueError('Username does not exist!')
            # Check password
            if not check_password_hash(user.user_pwd,pwd):
                raise ValueError('Incorrect password!')
            # If everything is okay, set session variable
            session['isonline'] = user.id
            flash('You have successfully logged in', category='success')
            return redirect(url_for('home'))
        except ValueError as ve:
            flash(str(ve), category='error')
        except Exception as e:
            app.logger.error(f"Error during user login: {str(e)}", exc_info=True)
            flash(f'An error occurred while logging in. Please try again later.', category='error')
    return render_template('user/students/login.html')

# *********************************** USER LOGIN **************************************************


# *********************************** USER LOGOUT **************************************************
@app.route('/user/logout/')
@login_required
def user_logout():
    if session.get('isonline') != None:
        session.pop('isonline',None) 
        flash('You have successfully logged out', category='success')       
    return redirect(url_for('user_login'), 302)
# *********************************** USER LOGOUT **************************************************

# *********************************** UPDATE PROFILE **************************************************
@app.route('/update/profile/<int:id>/', methods=['GET', 'POST'])
@login_required
def update_profile(id):
    user = Users.query.get_or_404(id)
    departments = Department.query.all()

    if request.method == 'POST':
        try:
            # Get form data
            fname = request.form.get('fname', '').strip()
            lname = request.form.get('lname', '').strip()
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            faculty = request.form.get('faculty')
            dept_id = request.form.get('department')
            level = request.form.get('level')   # fixed: level separate from faculty
            bio = request.form.get('bio', '').strip()
            interest = request.form.get('interests', '').strip()
            pix = request.files.get('profile_pic')  # fixed: match HTML name

            # Update user names if provided
            if fname or lname:
                user.fname = fname.upper() if fname else user.fname
                user.lname = lname.upper() if lname else user.lname
                db.session.commit()

            # Handle profile picture upload
            img_name = None
            if pix and pix.filename:
                allowed_ext = ['.jpg', '.png', '.jpeg', '.webp']
                _, ext = os.path.splitext(pix.filename)
                if ext.lower() in allowed_ext:
                    img_name = secrets.token_hex(10) + ext
                    pix.save(os.path.join('pkg/static/uploads/profile', img_name))

            # Validate phone number (basic check)
            if phone and (not phone.isdigit() or len(phone) != 11):
                raise ValueError('Invalid phone number! It must be 11 digits.')

            # Get department object
            dept_obj = Department.query.filter_by(id=dept_id).first()

            # Fetch or create profile
            profile = Profile.query.filter_by(user_id=id).first()
            if not profile:
                profile = Profile(user_id=id)
                db.session.add(profile)

            # Update profile fields
            profile.faculty = faculty
            profile.level = level
            profile.phone = phone
            profile.address = address
            if dept_obj:
                profile.dept_id = dept_obj.id
            profile.bio = bio
            profile.interest = interest
            if img_name:
                profile.pix = img_name

            db.session.commit()
            flash('Profile updated successfully', category='success')
            return redirect(url_for('update_profile', id=id))

        except Exception as e:
            app.logger.error(f"Error during profile update: {str(e)}", exc_info=True)
            flash(f'An error occurred while updating profile. Please try again later. {str(e)}',
                  category='error')

    return render_template('user/profile.html', user=user,
                           department=departments)
# *********************************** UPDATE PROFILE **************************************************

# *********************************** USER LIKE/UNLIKE **************************************************
@app.route('/toggle_like', methods=['POST'])
def toggle_like():
    if 'isonline' not in session:
        return jsonify({'error': 'Login required'}), 401

    user_id = session['isonline']
    post_id = request.json.get('post_id')

    post = Posts.query.get(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    like = Likes.query.filter_by(user_id=user_id, post_id=post_id).first()

    if like:
        db.session.delete(like)
        db.session.commit()
        liked = False
    else:
        db.session.add(Likes(user_id=user_id, post_id=post_id))
        db.session.commit()
        liked = True

    like_count = Likes.query.filter_by(post_id=post_id).count()
    return jsonify({'liked': liked, 'like_count': like_count})

# *********************************** USER LIKE/UNLIKE **************************************************

# *********************************** USER COMMENTS **************************************************

@app.route('/comment', methods=['POST'])
def comment():
    if 'isonline' not in session:
        flash("Please login to comment.")
        return redirect(url_for('login'))

    post_id = request.form.get('post_id')
    comment_text = request.form.get('comment')

    if not post_id or not comment_text.strip():
        flash("Comment cannot be empty")
        return redirect(url_for('home'))

    new_comment = Comment(
        post_id=post_id,
        user_id=session['isonline'],  # your logged in user
        text=comment_text.strip()
    )
    db.session.add(new_comment)
    db.session.commit()

    flash("Comment added successfully!")
    return redirect(url_for('home'))

# *********************************** USER COMMENTS **************************************************#

# *********************************** USER PROFILE **************************************************#
@app.route('/user/profile/<int:id>/')
@login_required
def profile(id):
    user = Users.query.get(id)
    # To get the department of the user using relationship
    profile = Profile.query.filter_by(user_id=id).first()
    if profile and profile.dept_id:
        department = Department.query.get(profile.dept_id)
    else:
        department = None
    return render_template('user/seeprofile.html', user=user, profile=profile, department=department)
# *********************************** USER PROFILE **************************************************#

# *********************************** VC SIGNUP **************************************************#
@app.route('/vc/login/', methods=['GET','POST'])
def vc_login():
    if request.method == 'POST':
        try:
            uname = request.form.get('uname','').strip()
            pwd = request.form.get('pwd','').strip()

            if not uname or not pwd:
                raise ValueError('Input fields cannot be empty')
            # Check if user exists
            user = Users.query.filter((Users.username == uname) | (Users.email == uname)).first()
            # user = Users.query.filter(or_(Users.username==uname,Users.email==uname)).first()
            if not user:
                raise ValueError('Username does not exist!')
            # Check password
            if not check_password_hash(user.user_pwd,pwd):
                raise ValueError('Incorrect password!')
            # If everything is okay, set session variable
            session['vconline'] = user.id
            session['isonline'] = user.id

            flash('You have successfully logged in', category='success')
            return redirect(url_for('announcement'))
        except ValueError as ve:
            flash(str(ve), category='error')
        except Exception as e:
            app.logger.error(f"Error during user login: {str(e)}", exc_info=True)
            flash(f'An error occurred while logging in. Please try again later.', category='error')
    return render_template('user/vc/vc_login.html')
# *********************************** VC SIGNUP **************************************************#

# *********************************** VC ANNOUNCEMENT **************************************************#
@app.route('/vc/announcement/', methods=['GET','POST'])
@login_required
def announcement():
    if session.get('vconline') == None:
        flash('You need to be logged in as VC before you can visit page', category='error')
        return redirect(url_for('vc_login'))

    user_id = session['vconline']
    announcements = db.session.query(Announcement).order_by(Announcement.date_posted.desc()).all()

    # Dictionary of liked posts for this user

    if request.method == 'POST':
        try:
            content = request.form.get('announcement')
            title = request.form.get('title')

            if not content or content.strip() == '':
                raise ValueError('Announcement field cannot be empty')
            if not title or title.strip() == '':
                raise ValueError('Title field cannot be empty')
            
            announcement = Announcement(title=title,
                                        content=content)
            db.session.add(announcement)
            db.session.commit()

            flash('Announcement sent', category='success')
            return redirect(url_for('announcement'))
            

        except ValueError as e:
            app.logger.error(f"Message: {str(e)}", exc_info=True)
            flash(f'{str(e)}', category='error')
        except Exception as e:
            app.logger.error(f"Error during user signup: {str(e)}", exc_info=True)
            flash(f'An error occured during upload try again later {str(e)}', category='error')
    return render_template('user/vc/vc_announcement.html',announcements=announcements, user_id=user_id)
# *********************************** VC ANNOUNCEMENT **************************************************#
