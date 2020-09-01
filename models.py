from app import db
from app import MAX_ID_VALUE


class Link(db.Model):
    """
    We are not required to store the shortlink that we give to a user.
    This is because the link_id is encoded deterministically in base 57
    and can decoded with ease.
    """
    link_id = db.Column(
        db.Integer,
        db.Sequence('seq_link_id', start=0, maxvalue=MAX_ID_VALUE),
        primary_key=True
    )
    long_url = db.Column(db.String(1024), nullable=False)

