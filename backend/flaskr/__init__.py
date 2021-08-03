import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import CORS
import random

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
        # page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        question_list = [question.format() for question in questions]
        current_questions = question_list[start:end]

        return current_questions

    '''
    @TODO: 
    Create an endpoint to handle GET requests 
    for all available categories.
    '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
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

    '''
    @TODO: 
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''
    @app.route('/questions', methods=['GET'])
    def get_questions():
        page_num = request.args.get('page', 1, type=int)

        try:
            questions = Question.query.all()
        except SQLAlchemyError:
            abort(500)
        finally:
            selected_questions = paginate_questions(page_num, questions)

            ''' This code does nothing but set category to 1, revisit this! '''
            current_category = None  # request.data['currentCategory']
            # see if current category is set
            if current_category:
                current_category = int(current_category)
            else:
                current_category = 1

            #
            category = Category.query.filter(Category.id == current_category).one_or_none()
            db_categories = Category.query.all()

            # need a list of categories in text from the db objects
            categories = {}
            for item in db_categories:
                categories[item.id] = item.type

            # what to do if there are no categories?

            if category == None:
                # need to handle the case where the category didn't exist
                pass

            return jsonify({
                'questions': selected_questions,
                'total_questions': len(questions),
                'categories': categories,
                'category': categories[current_category]
            })

    '''
    @TODO: 
    Create an endpoint to DELETE question using a question ID. 
  
    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''

    @app.route('/questions/<question_id>', methods=['DELETE'])
    def delete_question(question_id):
        Question.query.filter(Question.id==question_id).delete()
        db.session.commit()

        return jsonify({
            'success': True
        })



    '''
    @TODO: 
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score.
  
    TEST: When you submit a question on the "Add" tab, 
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.  
    '''
    @app.route('/addquestion', methods=['POST'])
    def add_new_question():
        json_data = request.get_json()

        # # we have a text category, need the id of the category to set the question's category as an int
        # categories = Category.query.filter(Category.type == json_data['category']).one_or_none()
        #
        # # the interface doesn't provide a way to warn that the category doesn't exist, so just assign it
        # for category in categories:
        #     if category.type == json_data['category']:
        #         category_id = category.id

        new_question = Question(
                question=json_data['question'],
                answer=json_data['answer'],
                difficulty=json_data['difficulty'],
                category=int(json_data['category']) + 1
        )

        db.session.add(new_question)
        db.session.commit()

        return jsonify({
            'success': True
        })

    '''
    @TODO: 
    Create a POST endpoint to get questions based on a search term. 
    It should return any questions for whom the search term 
    is a substring of the question. 
  
    TEST: Search by any phrase. The questions list will update to include 
    only question that include that string within their question. 
    Try using the word "title" to start. 
    '''
    @app.route('/questions', methods=['POST'])
    def search_questions():
        json_data = request.get_json()
        search_term = '%' + json_data['searchTerm'] + '%'

        # find matches for searchTerm in Question, use ilike on db for case-insensitive search
        question_matches = Question.query.filter(Question.question.ilike(search_term)).all()

        question_list = []

        for question in question_matches:
            question_list.append({'question':question.question})

        # NOTE: we return None for category per https://knowledge.udacity.com/questions/645582
        return jsonify({
            'questions': question_list,
            'total_questions': len(question_matches),
            'current_category': None,
            'category': None
        })

    '''
    @TODO: 
    Create a GET endpoint to get questions based on category. 
  
    TEST: In the "List" tab / main screen, clicking on one of the 
    categories in the left column will cause only questions of that 
    category to be shown. 
    '''
    @app.route('/categories/<int:id>/questions', methods=['GET'])
    def get_questions_by_category(id):

        # NOTE: we don't paginate questions when displayed by category

        # because the id is sent by the user clicking an existing category, we assume it exists
        questions = Question.query.filter(Question.category == id).all()
        questions_list = [question.question for question in questions]

        category = Category.query.filter(Category.id == id).one_or_none()

        current_category = category.type

        return jsonify({
            'questions': questions_list,
            'total_questions': len(questions),
            'current_category': current_category
        })


    '''
    @TODO: 
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 
  
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not. 
    '''

    '''
    @TODO: 
    Create error handlers for all expected errors 
    including 404 and 422. 
    '''
    '''
    
    '''
    @app.errorhandler()
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "unprocessable"
        }), 404

    '''
    
    '''
    @app.errorhandler()
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    '''
    
    '''
    @app.errorhandler()
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "unprocessable"
        }), 500

    return app

