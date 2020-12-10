# Temp routes for development

@main.route('/add_accents')
def add_accents():
    # Reset
    InternationalAccent.query.delete()

    # Add all the International Accents into the database
    for item in international_accent_list:
        id = int(item['id'])
        character = item['character']
        try:
            html_entity = item['entitycode']
        except:
            html_entity = ''
        try:
            alt_code = item['altcode']
        except:
            alt_code = ''
        language = item['language']
        row_num = item['rownum']
        in_use = item['inuse']

        special_character = InternationalAccent(id=id, character=character, language=language, alt_code=alt_code, html_entity=html_entity, row_num=row_num, in_use=in_use)
        db.session.add(special_character)
                
    db.session.commit()
    db.session.close()

    return redirect(url_for('main.list', lng='en'))


@main.route('/hard_delete_all')
def hard_delete_all():

    UserExample.query.delete()
    Word.query.delete()
    BulkTranslate.query.delete()
    User.query.delete()
    
    db.session.commit()
    db.session.close()

    return redirect(url_for('main.index'))


@main.route('/init')
def init():
    # INITIALIZE DATABASE WITH STARTING DATA
    test_user_email = 'test1000@gmail.com'
    test_user_exists = User.query.filter_by(email=test_user_email).first()

    if not test_user_exists:
        user = User(email=test_user_email, 
                    username='test1000',
                    password='12341234')
        db.session.add(user)
        db.session.commit()

    accent_exists = InternationalAccent.query.filter_by(html_entity='Agrave;').first()

    # Add all the International Accents into the database
    if not accent_exists:
        for item in international_accent_list:
            id = int(item['id'])
            character = item['character']
            html_entity = item['entitycode']
            alt_code = item['altcode']
            language = item['language']
            row_num = item['rownum']
            in_use = item['inuse']

            special_character = InternationalAccent(id=id, character=character, language=language, alt_code=alt_code, html_entity=html_entity, row_num=row_num, in_use=in_use)
            db.session.add(special_character)
                
        db.session.commit()

    test_user = User.query.filter_by(email=test_user_email).scalar()
    # These is a more efficient way to do this with the load_only function https://code-examples.net/en/q/afefd4
    test_user_id = test_user.id
    has_data = UserExample.query.filter_by(user_id=test_user_id).first()
    all_examples = UserExample.query.filter_by(user_id=test_user_id).all()

    # If it's the same length, don't add any more
    if len(starting_data) != len(all_examples):
        # Reset the data by deleting whatever is already there
        UserExample.query.filter_by(user_id=test_user_id).delete()
        for item in starting_data:
            language = item['language']
            word = item['word']
            example = item['example']

            if language == 'english':
                # Check word already exists
                # use first() instead of one() https://stackoverflow.com/questions/24985989/check-if-one-is-empty-sqlalchemy
                word_already_exists_in_db = Word.query.filter_by(word=word).first()
                if not word_already_exists_in_db:
                    record_word = Word(word=word, etymology='', pronunciation='')
                    db.session.add(record_word)

                    word_query_inefficient = Word.query.filter_by(word=word).one()
                    last_row_id_inefficient = word_query_inefficient.id

                    record_user_example = UserExample(example=example, word=word, word_id=last_row_id_inefficient, user_id=test_user_id, translation=False, src=None, dst='en')

                    db.session.add(record_user_example)

            else:
                dst = item['dst']
                record = UserExample(example=example, word=word, word_id=None, user_id=test_user_id, translation=True, src='en', dst=dst)
                db.session.add(record)

        db.session.commit()
    
    db.session.close()

    return render_template('index.html')    