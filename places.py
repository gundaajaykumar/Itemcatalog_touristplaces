from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_setup import Tourism, Base, Destination, User

engine = create_engine('sqlite:///skytravels.db')

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()

session = DBSession()

# create a user

User1 = User(name='ajay', email='15pa1a0454@vishnu.edu.in')

# List of tourist spots

tourist1 = Tourism(name='Uttar Pradesh')

session.add(tourist1)
session.commit()

spot1 = Destination(name='Taj Mahal',
                    details='An ivory-white marble mausoleum',
                    charge='Rs.5000', course='mosque', tourist=tourist1)

session.add(spot1)
session.commit()
spot2 = Destination(name='Agra Fort', details='Residence of \
                     the emperors of the Mughal Dynasty',
                    charge='Rs.8000', course='fort', tourist=tourist1)

session.add(spot2)
session.commit()
spot3 = Destination(name="Akbar's Tomb",
                    details='Tomb of the Mughal emperor',
                    charge='Rs.2000', course='fort', tourist=tourist1)

session.add(spot3)
session.commit()

tourist2 = Tourism(name='Maharashtra')

session.add(tourist2)
session.commit()

spot1 = Destination(name='Shirdi',
                    details='Holiest places in\
                    India and also one of the popular pilgrimage',
                    charge='Rs.3000', course='piligrimage',
                    tourist=tourist2)

session.add(spot1)
session.commit()
spot2 = Destination(name=' Ellora Caves',
                    details="Ancient historical\
                    caves locally known as 'Verul Leni'",
                    charge='Rs.7000', course='seenary',
                    tourist=tourist2)

session.add(spot2)
session.commit()
spot3 = Destination(name='Nashik',
                    details='Situated on the banks of River Godavari',
                    charge='Rs.6000', course='piligrimage',
                    tourist=tourist2)

session.add(spot3)
session.commit()
tourist3 = Tourism(name='Tamil Nadu')

session.add(tourist3)
session.commit()

spot1 = Destination(name='Kanchipuram',
                    details='The city served as\
                    the capital of Pallava Dynasty',
                    charge='Rs.5500', course='piligrimage',
                    tourist=tourist3)

session.add(spot1)
session.commit()
spot2 = Destination(name='Chennai', details="Capital city'",
                    charge='Rs.7500', course='seenary',
                    tourist=tourist3)

session.add(spot2)
session.commit()
spot3 = Destination(name='Chidambaram',

                    details='Well known for Nataraja Temple',
                    charge='Rs.6500', course='piligrimage',
                    tourist=tourist3)

session.add(spot3)
session.commit()
tourist4 = Tourism(name='Andhra Pradesh')

session.add(tourist4)
session.commit()

spot1 = Destination(name='Talakona falls', details='Water falls',
                    charge='Rs.9000', course='seenary',
                    tourist=tourist4)

session.add(spot1)
session.commit()
spot2 = Destination(name='Tirupati', details='home of Lord Venkateswara',
                    charge='Rs.10000', course='piligrimage',
                    tourist=tourist4)

session.add(spot2)
session.commit()
spot3 = Destination(name='Lepakshi',
                    details='Reign of the Vijayanagara king',
                    charge='Rs.9500', course='piligrimage',
                    tourist=tourist4)

session.add(spot3)
session.commit()
print 'Tourist places'
