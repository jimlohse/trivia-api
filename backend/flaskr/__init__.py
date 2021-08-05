import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import CORS
import random
import werkzeug

from models import db, setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    CORS(app)  # allows * by default

    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    def paginate_questions(page, questions):
        ''' Returns a selection of all questions that fit on one page

        Keyword arguments:
        :param page: the page number to return questions for
        :param questions: all the questions, a selection of which is returned
        :return: current list of questions
        '''
        # page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        question_list = [question.format() for question in questions]
        current_questions = question_list[start:end]

        return current_questions

    @app.route('/categories', methods=['GET'])
    def get_categories():
        ''' Returns a JSON-based list of categories, used by quiz pages that list categories

        :return: JSON list of categories
        '''
        try:
            categories = Category.query.all()
        except SQLAlchemyError:
            abort(500)
        finally:
            # make a list out of the categories returned from the db
            categories_list = [category.type for category in categories]

            return jsonify({
                'categories': categories_list
            })

    @app.route('/questions', methods=['GET'])
    def get_questions():
        ''' Gets the questions for a specific page of questions being displayed

        :return: JSON-based list of questions and other properties related to the returned questions
        '''
        page_num = request.args.get('page', 1, type=int)

        try:
            questions = Question.query.all()
        except SQLAlchemyError:
            abort(500)
        finally:
            selected_questions = paginate_questions(page_num, questions)
            current_category = 1

            category = Category.query.filter(Category.id == current_category).one_or_none()
            db_categories = Category.query.all()

            # need a list of categories in text from the db objects
            categories = {}
            for item in db_categories:
                categories[item.id] = item.type

            return jsonify({
                'questions': selected_questions,
                'total_questions': len(questions),
                'categories': categories,
                'category': categories[current_category]
            })

    @app.route('/add_question', methods=['POST'])
    def add_new_question():
        ''' Adds a question using POST method.'''
        json_data = request.get_json()

        new_question = Question(
                question=json_data['question'],
                answer=json_data['answer'],
                difficulty=json_data['difficulty'],
                category=int(json_data['category']) + 1
        )

        try:
            db.session.add(new_question)
            db.session.commit()
        except SQLAlchemyError:
            abort(500)

        return jsonify({
            'success': True,
            'id': new_question.id
        })

    @app.route('/questions/<question_id>', methods=['DELETE'])
    def delete_question(question_id):
        ''' Deletes a specified question from the database

        :param question_id: The DB id of the question to be deleted
        :return: JSON-based success message
        '''
        try:
            question_id = int(question_id)
            Question.query.filter_by(id=question_id).delete()
            db.session.commit()
        except:
            abort(500)

        return jsonify({
            'success': True
        })

    @app.route('/questions', methods=['POST'])
    def search_questions():
        ''' Performs a case-insensitive search of the questions for the search term.
        Looks for anything that contains the search term, does not need exact match.

        :return: Returns the questions that match the search term in a dict in JSON
        also returns number of questions returned and category
        '''
        json_data = request.get_json()
        search_term = '%' + json_data['searchTerm'] + '%'

        # find matches for searchTerm in Question, use ilike on db for case-insensitive search
        question_matches = Question.query.filter(Question.question.ilike(search_term)).all()

        question_list = []

        for question in question_matches:
            question_list.append({
                'id': question.id,
                'question': question.question,
                'answer': question.answer,
                'category': question.category,
                'difficulty': question.difficulty
            })

        # NOTE: we return None for category per https://knowledge.udacity.com/questions/645582
        return jsonify({
            'questions': question_list,
            'total_questions': len(question_matches),
            'current_category': None,
            'category': None
        })

    @app.route('/categories/<int:id>/questions', methods=['GET'])
    def get_questions_by_category(id):
        ''' Questions are returned by category, for a given category. NOTE: we don't paginate
        questions when displayed by category because the id is sent by the user clicking an
        existing category, we assume it exists
        :param id: The database id of the category to return questions for
        :return: JSON of questions, total number of questions and category of questions
        '''
        questions = Question.query.filter(Question.category == id).all()

        questions_list = []

        for question in questions:
            questions_list.append({
                'id': question.id,
                'question': question.question,
                'answer': question.answer,
                'category': question.category,
                'difficulty': question.difficulty
            })

        category = Category.query.filter(Category.id == id).one_or_none()

        current_category = category.type

        return jsonify({
            'questions': questions_list,
            'total_questions': len(questions),
            'current_category': current_category
        })

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():
        ''' Gets questions from given category and presents questions that haven't been asked yet.
        If ALL is chosen, then request type is "click" and all questions are presented, one at a
        time. Questions are randomized to be presented in a different order during each game.'''
        json_data = request.get_json()

        previous_questions = json_data['previous_questions']
        category = json_data['quiz_category']
        # need to add one to category, in the db they are 1-indexed, set category_id
        category_id = int(category['id']) + 1

        # look to find a question that hasn't been asked and return it as question_to_return
        # if category type is 'click', we look at all categories / all questions
        if category['type'] == 'click':
            try:
                questions = Question.query.order_by(Question.id).all()
            except SQLAlchemyError:
                abort(500)
        # else if category is non-zero, we look at a specific category
        else:
            try:
                questions = Question.query.filter(Question.category == category_id).order_by(Question.id).all()
            except SQLAlchemyError:
                abort(500)

        # randomize questions
        random.shuffle(questions)

        question_to_return = None
        for question in questions:
            if question.id not in previous_questions:
                question_to_return = question
                break

        # need to check if all the questions were used up and question_to_return is None
        # if question_to_return is None:
        if question_to_return is None:
            question_dict = None
        else:
            question_dict = {
                'id': question_to_return.id,
                'question': question_to_return.question,
                'answer': question_to_return.answer,
                'difficulty': question_to_return.difficulty,
                'category': question_to_return.category
            }

        return jsonify({
            'question': question_dict
        })

    @app.errorhandler(werkzeug.exceptions.BadRequest)
    def handle_bad_request(e):
        ''' Werkzeug 400 error handler for 400 errors -- usually these are bad routes. '''
        return 'bad request!', 400

    @app.errorhandler(404)
    def not_found(error):
        ''' Handles 404 errors, indicating a route was chosen that doesn't match any routes'''
        return jsonify({
            "success": False,
            "error": 404,
            "message": "not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        ''' Handles 422 errors, which are not currently thrown by any "try...except" clause. '''
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def internal_error(error):
        ''' Handles 500 errors, usually are database errors caught by except clause. '''
        return jsonify({
            "success": False,
            "error": 500,
            "message": "unprocessable"
        }), 500

    return app

