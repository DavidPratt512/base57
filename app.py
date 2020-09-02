import os
import random
from datetime import datetime
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
from math import log


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

BUTTON_TEXT = [
    'Shorten me!',
    'Shrink me!',
    'Honey, I shrunk the URL!',
    'Minify this!',
]

# Normal base 62 alphabet without 0, 1, l, I, O characters, making
# this alphabet base 57. With 4 digits of base 57, 57**4 url's can 
# be stored (~10.5 million). The alphabet is randomized so that
# shortened urls appear to not follow any obvious pattern.
ALPHABET = 'hAgVMdBcvXPiaH7QNpko5qz8ts4TWu62yx3GCDRnSmbUYerFJEZLwf9Kj'
ENCODE_BASE = len(ALPHABET)
SHORT_URL_LENGTH = 4
TOTAL_BUCKETS = ENCODE_BASE ** SHORT_URL_LENGTH
MAX_ID_VALUE = TOTAL_BUCKETS - 1
# This scalar has the necessary property:
# gcd(SCALAR, TOTAL_BUCKETS)= 1.
SCALAR = 3141592
# equivalent to pow(SCALAR, -1, TOTAL_BUCKETS) in python 3.8+
SCALAR_INVERSE = 5252017


from models import Link


def encode(n, reversed_digits=None):
    """
    Converts a non-negative integer n to base ENCODE_BASE using the
    symbols in ALPHABET. ALPHABET[0] corresponds to the 'zero' value
    in ALPHABET.
    """
    # To convert a positive decimal integer N to base b, find the
    # largest power p of b such that b ** p < N. This is always
    # floor(log_b(N)). Proceed to find how many times b ** p divides
    # into N, call this quantity m. In base b, the digit in the p-th
    # position will have value m. Recursively convert the quantity
    # N - m*(b**p) to base b. This will fill in the remaining digits.
    global ALPHABET
    global ENCODE_BASE
    global SHORT_URL_LENGTH

    fill_width = SHORT_URL_LENGTH

    if n == 0 and reversed_digits is None:
        return (ALPHABET[0] * (fill_width - 1)) + ALPHABET[0]
    elif n == 0:
        return ''.join(reversed(reversed_digits))

    # p is the largest integer such that ENCODE_BASE ** p < n
    p = int(log(n, ENCODE_BASE))

    if reversed_digits is None:
        # create a list filled with zero-values and (p + 1) elements
        reversed_digits = ([ALPHABET[0]] * (p + 1)) + ([ALPHABET[0]] * (fill_width - p - 1))

    # m is 'how many times' a power of the ENCODE_BASE 'goes into' n
    m = n // (ENCODE_BASE ** p)
    reversed_digits[p] = ALPHABET[m]
    return encode(n - (m * (ENCODE_BASE ** p)), reversed_digits)


def to_decimal(digit_string):
    """
    Converts a non-negative integer digit string that is written using
    ALPHABET into an integer base 10.
    """
    global ALPHABET
    global ENCODE_BASE
    # assign values in the ALPHABET to numeric values
    alpha_values = {sym: i for i, sym in enumerate(ALPHABET)}

    return sum(
        alpha_values[digit] * (ENCODE_BASE ** p)
        for p, digit in enumerate(reversed(digit_string))
    )


def decode(short_url):
    """
    Decodes the short_url into the corresponding id in the Link table.
    """
    global ALPHABET
    global SCALAR
    global SCALAR_INVERSE
    global TOTAL_BUCKETS

    # turn the shortlink back into an integer, but we still need the
    # ID that generated this link.
    decimal_conversion = to_decimal(short_url)

    # solve the modular congruence
    # SCALAR * ID = decimal_conversion    (mod TOTAL_BUCKETS)
    # for ID using the modular inverse of SCALAR
    return (decimal_conversion * SCALAR_INVERSE) % TOTAL_BUCKETS


def httpify(url):
    """
    Prepends 'http://' to a url if 'http(s)://' is not present at the
    start of the string.
    """
    if not (url.startswith('https://') or url.startswith('http://')):
        return f'http://{url}'
    else:
        return url


@app.route('/', methods=['GET'])
def index_get():
    return render_template('index.html', button_text=random.choice(BUTTON_TEXT))


@app.route('/', methods=['POST'])
def index_post():
    long_url = httpify(request.form['url-input'])
    link = Link(long_url=long_url)

    try:
        db.session.add(link)
        db.session.commit()
        short_url = encode((SCALAR * link.link_id) % TOTAL_BUCKETS)
        return render_template('index.html', button_text=random.choice(BUTTON_TEXT), long_url=long_url, short_url=short_url)
    except Exception as e:
        return render_template('index.html', button_text=random.choice(BUTTON_TEXT), long_url=long_url, short_url=e)


@app.route('/<string:short_url>')
def redirect_from_short_url(short_url):
    if len(short_url) != 4:
        return render_template('404.html'), 404
    link_id = decode(short_url)
    long_url = Link.query.get_or_404(link_id).long_url
    return redirect(long_url, code=302)


@app.route('/about')
def about():
    return render_template('about.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(threaded=True)

