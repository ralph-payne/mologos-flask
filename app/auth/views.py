from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm


## This is the code that blocks the user from hitting the site if they are not confirmed ##
# @auth.before_app_request
# def before_request():
#     if current_user.is_authenticated:
#         # Update last seen with ping
#         current_user.ping()
#         if not current_user.confirmed \
#                 and request.endpoint \
#                 and request.blueprint != 'auth' \
#                 and request.endpoint != 'static':
#             return redirect(url_for('auth.unconfirmed'))


# @auth.route('/unconfirmed')
# def unconfirmed():
#     # if current_user.is_anonymous or current_user.confirmed:
#     if current_user.is_anonymous:
#         return redirect(url_for('main.index'))
#     return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            flash(f'Invalid email address', 'flash-danger')
            return render_template('auth/login.html', form=form)
        if user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        else:
            flash('Invalid password', 'flash-danger')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'flash-success')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'GET':
        return render_template('auth/register.html', form=form)

    else:
        if (form.password1.data != form.password2.data):
            flash('Passwords must match', 'flash-danger')
            return render_template('auth/register.html', form=form)

        if (len(form.username.data)) < 4:
            flash('Username should be longer than 3 characters', 'flash-danger')
            return render_template('auth/register.html', form=form)

        # Look up if email is already taken
        email_check = User.query.filter_by(email=form.email.data.lower()).first()

        if (email_check):
            flash(f'{form.email.data.lower()} is already in use', 'flash-danger')

        username_check = User.query.filter_by(username=form.username.data.lower()).first()

        if (username_check):
            flash(f'{form.username.data.lower()} is already in use', 'flash-danger')

        if (len(form.password1.data)) < 7:
            flash('Password should be longer than 6 characters', 'flash-danger')

        if form.validate_on_submit():
            user = User(email=form.email.data.lower(),
                        username=form.username.data,
                        password=form.password1.data)
            db.session.add(user)
            db.session.commit()

            ## auto generated email - not in use ##
            # token = user.generate_confirmation_token()
            # send_email(user.email, 'Confirm Your Account',
            #         'auth/email/confirm', user=user, token=token)
            # flash(f'A confirmation email has been sent to {form.email.data.lower()}', 'flash-success')
            ## end of auto generated email block ##

            flash(f'You have registered with {form.email.data.lower()}', 'flash-success')
            return redirect(url_for('auth.login'))

        return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
            'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token)
        flash('An email with instructions to reset your password has been '
              'sent to you.', 'flash-success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.')
    return render_template('auth/change_email.html', form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))