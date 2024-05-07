# Photo Share

## Description

Photo Share is a web application that allows users to share and discover photos.

## Features

- User authentication: Users can create accounts, log in, and log out.
- Image upload: Users can upload images to share with others.
- Image comment: Users can leave comments under each others images.
- Image search: Users can search for images by keyword or tag.
- Image rating: Users can rate images uploaded by others.


## Technologies Used

- Python
- FastAPI
- PostgreSQL (for the database)
- Docker (for containerization)
- Other dependencies listed in `requirements.txt` and `package.json`

## Installation

To run the Photo Share project locally, follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/Martizia/PhotoShare-by-Rapid-Creators
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   Create file `.env` using `.env.example`.


3. Set up the database:
   - Run `docker-compose up -d` to create Docker container.
   - Create a PostgreSQL database named `photo_share` or other name that you put in your `.env` file.
   - Run `alembic upgrade head` to install migration in DB.
   

4. Run the application:
   ```sh
   uvicorn main:app --host localhost --port 8000 --reload
   ```

5. Access the application at `http://localhost:8000` or `127.0.0.1:8000` in your web browser.

## Usage

1. Register for an account on the Photo Share website.
2. Log in with your credentials.
3. Upload images to share with others.
4. Search for images by keyword or tag.
5. Rate images uploaded by other users.

## API Documentation

The API documentation for the Photo Share project is available at `http://localhost:8000/docs` or `http://127.0.0.1:8000/docs#/` when the application is running.

## Contributing

Contributions to Photo Share are welcome! To contribute, please follow these guidelines:
- Fork the repository
- Create a new branch (`git checkout -b feature`)
- Make your changes
- Commit your changes (`git commit -am 'Add new feature'`)
- Push to the branch (`git push origin feature`)
- Create a new Pull Request
