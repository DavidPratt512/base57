# base57 - URL Shortener

This small app uses Flask and PostgreSQL to shorten URLS.


## About

Instead of using base 62 (digits + uppercase letters + lowercase letters), throw out the 5 lookalike characters to be left with base 57.
The general idea is to encode a URL **uniquely** and **deterministically** in base 57.
This is accomplished by assigning an integer ID automatically (auto-incrementally) by the database to each client URL.

Any integer can be converted to base 57, but to make things fancy, by commiting to using only 4 'digits' of base 57 for each short link, one can use the magic of modular arithmetic to uniquely and deterministically map any integer to a set of numbers ranging from 0 to 57^4.
Decoding also requires magic.
