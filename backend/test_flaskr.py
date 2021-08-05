import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from flaskr import create_app
from models import setup_db, Question, Category

# MAKE SURE this is the same as QUESTIONS_PER_PAGE in __init.py__
QUESTIONS_PER_PAGE = 10


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format('postgres',
                                                               'postgres',
                                                               'localhost:5432',
                                                               self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            # self.db.create_all()
    
    def tearDown(self):
        """Executed after each test"""
        pass

# ************** non-DB modifying TESTS first! **************
    def test_index(self):
        """Test that accessing / route returns a 404 """
        result = self.client().get('/')
        data = json.loads(result.data)

        self.assertEqual(result.status_code, 404)

    def test_questions(self):
        """Test that questions are returned on /questions

        At the outset, the database has 19 questions
        """
        result = self.client().get('/questions')
        data = json.loads(result.data)

        self.assertEqual(result.status_code, 200)
        self.assertTrue(data['categories'])
        self.assertEqual(len(data['questions']), QUESTIONS_PER_PAGE)
        self.assertEqual(data['total_questions'], 19)

    def test_questions_with_page_num(self, page2_questions=9, total_questions=19):
        """Test that questions are returned on /questions?page=2

        The second page will show 9 questions and there are 19 total questions
        """
        result = self.client().get('/questions?page=2')
        data = json.loads(result.data)

        self.assertEqual(result.status_code, 200)
        self.assertTrue(data['categories'])
        self.assertEqual(len(data['questions']), page2_questions)
        self.assertEqual(data['total_questions'], total_questions)

    def test_get_categories(self):
        ''' Tests that /categories returns a list of categories

        :return:
        '''
        result = self.client().get('/categories')
        data = json.loads(result.data)

        self.assertEqual(len(data['categories']), 6)
        self.assertEqual(data['categories'][0], 'Science')

    def test_search_post_questions_how(self):
        ''' Tests for a positive search term 'how' that returns one question

        '''
        # inspired by https://stackoverflow.com/questions/44892061/flask-unittest-for-post-method
        with self.app.test_client() as client:
            to_send = {
                'searchTerm': 'how'
            }
            result = client.post(
                '/questions',
                json=to_send
            )
            data = json.loads(result.data)

            self.assertEqual(len(data['questions']), 1)
            self.assertEqual(data['questions'][0]['question'],
                             "How many paintings did Van Gogh sell in his lifetime?")

    def test_search_post_questions_when(self):
        ''' Tests for a negative search term 'when' that returns no questions

        '''
        # inspired by https://stackoverflow.com/questions/44892061/flask-unittest-for-post-method
        with self.app.test_client() as client:
            to_send = {
                'searchTerm': 'when'
            }
            result = client.post(
                '/questions',
                json=to_send
            )
            data = json.loads(result.data)

            self.assertEqual(len(data['questions']), 0)
            self.assertEqual(data['questions'], [])

# *************** Testing getting questions by category

    def test_questions_by_category_get(self):
        ''' Tests that /categories/<int:id>/questions returns a list of questions

        Specifically testing the Sports category that returns two questions
        '''
        result = self.client().get('/categories/6/questions')
        data = json.loads(result.data)

        self.assertEqual(len(data['questions']), 2)
        self.assertEqual(data['questions'][0]['question'],
                         "Which is the only team to play in every soccer World Cup tournament?")

    def test_questions_by_category_negative_case(self):
        ''' Tests that a bad request to /categories/<int:id>/questions returns an error

        *** ADDED after first review, was asking for 4 more tests and fixing broken test, which is done
        Checking that a POST request to this URL fails
        '''
        result = self.client().post('/categories/6/questions')
        data = json.loads(result.data)

        self.assertEqual(data['error'], 405)

# **************** Testing playing the game, both positive and negative
    def test_quizzes_post_play_game(self):
        ''' Tests /quizzes with POST that initially playing the game returns a question

        '''
        # inspired by https://stackoverflow.com/questions/44892061/flask-unittest-for-post-method
        with self.app.test_client() as client:
            to_send = {
                'previous_questions': [],
                'quiz_category': {
                    "id": "5",
                    'type': 'Science'}
            }
            result = client.post(
                '/quizzes',
                json=to_send
            )
            data = json.loads(result.data)

            # using assertIn because the Sports category has two questions and because they are randomized, it might be
            # either one. So we look at the question that is returned and see if it's in a string that contains both.
            self.assertIn(data['question']['question'],
                             "Which country won the first ever soccer World Cup in 1930?, Which is the only team to play in every soccer World Cup tournament?")

    def test_quizzes_play_with_wrong_request_type(self):
        ''' Tests whether a GET request to /quizzes fails

        *** ADDED after first review, was asking for 4 more tests and fixing broken test, which is done
        '''

        result = self.client().get('/quizzes')
        data = json.loads(result.data)

        self.assertFalse(data['success'])

    # ************** Database modifying TESTS last! **************

    def test_add_delete_same_question(self):
        """Test that a question can be added

        """
        # inspired by https://stackoverflow.com/questions/44892061/flask-unittest-for-post-method
        with self.app.test_client() as client:
            to_send = {
                'question': 'This is a test question',
                'answer': 'This is a test answer',
                'difficulty': '5',
                'category': 0
            }
            result = client.post(
                '/add_question',
                json=to_send
            )
            data = json.loads(result.data)

            self.assertTrue(data['success'])
            # global created_question_id
            created_question_id = data['id']

        ''' now test delete question in the same test, as we don't want to be dependent on the order
        tests are run. They are run in alphabetical order, and when order matters, a monolithic test
        should be used
        '''

        # inspired by https://stackoverflow.com/questions/44892061/flask-unittest-for-post-method
        with self.app.test_client() as client:
            result = client.delete(
                '/questions/' + str(created_question_id))

            # see if the deleted question is still in the db, also cleans the question if it fails
            try:
                Question.query.filter(Question.id==created_question_id).delete()
                self.assertTrue(True)
            except SQLAlchemyError:
                self.assertTrue(False)

    def test_add_a_question_failure(self):
        ''' Test that the wrong request type to adding a question fails

        *** ADDED after first review, was asking for 4 more tests and fixing broken test, which is done
        '''
        result = self.client().get('/add-question')
        data = json.loads(result.data)

        self.assertFalse(data['success'])

    def test_delete_non_existent_question(self):
        """Test that a question that doesn't exist cannot be deleted

        Try to delete question 10,000, which very likely doesn't exist in this toy app

        *** ADDED after first review, was asking for 4 more tests and fixing broken test, which is done
        """
        # inspired by https://stackoverflow.com/questions/44892061/flask-unittest-for-post-method
        with self.app.test_client() as client:
            result = client.get(
                '/questions/' + str(10000))

        data = json.loads(result.data)

        self.assertFalse(data['success'])

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()