# Web app to visualize cyclists' offsadle time on Trackleaders.

## Usage
1. To install dependencies, do

	```
	$ pip install -r requirements.txt
	```

2. Install `redis`

    ```
    # on Debian
    $ apt-get install redis-server
    # OR on Mac with brew
    $ brew install redis
    # AND start the server
    $ redis-server 
    ```

3. Run server with

	```
	# it doesn't have to be localhost:5000 ...
	$ ./run localhost:5000
	```
4. Alternatively, you can run `Flask`'s development server with

	```
	$ python web.py
	```
