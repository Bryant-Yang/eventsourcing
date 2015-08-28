# Event sourcing in Python

[![Build Status](https://secure.travis-ci.org/johnbywater/eventsourcing.png)](https://travis-ci.org/johnbywater/eventsourcing)

A library for event sourcing written in Python.

## Install

Use pip to install the latest release from Python Package Index. For the example below, and to make the tests work, please also install sqlalchemy (which isn't required if events are persisted in Cassandra - forthcoming).

    pip install eventsourcing[sqlalchemy]

After installation, the tests should pass.

    python -m unittest discover eventsourcingtests -v

## Development

The project is hosted on GitHub.

* https://github.com/johnbywater/eventsourcing


## Motivation and Inspiration

Event sourcing is really fantastic, but there doesn't seem to be a general library for event sourcing in Python.
The 'rewind' package is coded to work with ZeroMQ. The 'event-store' looks to be along the right lines, but provides
an event store rather than a full library for event sourcing.

Although the event sourcing patterns are simple, and they can be rewritten for each project,
there are distinct cohesive mechanisms, for example replaying stored domain events into an up-to-date domain
entity, that can usefully be reused. Quoting from the "Cohesive Mechanism" pattern in Eric Evan's
Domain Driven Design:

"Partition a conceptually COHESIVE MECHANISM into a separate lightweight framework. Particularly watch
for formalisms for well-documented categories of of algorithms. Expose the capabilities of the framework
with an INTENTION-REVEALING INTERFACE. Now the other elements of the domain can focus on expressing the problem
("what"), delegating the intricacies of the solution ("how") to the framework."

Inspiration:

* Martin Fowler's article on event sourcing
    * http://martinfowler.com/eaaDev/EventSourcing.html

* Robert Smallshire's example code on Bitbucket
    * https://bitbucket.org/sixty-north/d5-kanban-python/src

* Greg Young's discussions about event sourcing, and EventStore system
    * https://dl.dropboxusercontent.com/u/9162958/CQRS/Events%20as%20a%20Storage%20Mechanism%20CQRS.pdf
    * https://geteventstore.com/


## Features

* Base class for immutable domain events

* Generic immutable stored event type

* Function to get event topic from domain event class

* Function to resolve event topic into domain event class

* Function to serialize domain events to stored event objects

* Function to recreate domain events from stored event objects

* Base class for stored event repositories

    * Method to get all domain events in the order they occurred

    * Method to get all domain events for given entity ID, in the order they occurred

    * Method to get all domain events for given domain event topic

    * Method to get single domain event for given event ID

    * Method to get all domain events for given entity ID, from given version of the entity (forthcoming)

    * Method to delete of all domain events for given domain entity ID (forthcoming)

* Concrete stored event repository implementations for common database management systems (SQL and NoSQL)

    * Simple stored event repository, using simple Python objects for stored events (non-persistent)
    
    * SQLAlchemy stored event repository, using ORM to persist stored events in any supported database
    
    * Cassandra stored event repository, using a column family to persist stored events in Cassandra (forthcoming)
    
* Persistence subscriber class, to listen for published domain events and append them to its event store

* Event store class, to convert domain events to stored events appended to its stored event repository

* In-process publish-subscribe mechanism, for in-process domain event propagation to subscriber objects

* Base class for event sourced entities

* Base class for event sourced repositories

* Event player, to return a recreated domain entity for a given domain entity mutator and entity ID

* Update stored event (domain model migration) (forthcoming)

* Base class for event sourced applications

* Base event sourced application class, to have a stored event repository, an event store, a persistence subscriber, domain specific event sourced repositories and entity factory methods

* Examples (see below, more examples are forthcoming)

* Subscriber that publishes domain events to RabbitMQ (forthcoming)

* Subscriber that publishes domain events to Amazon SQS (forthcoming)

* Republisher that subscribes to RabbitMQ and publishes domain events locally (forthcoming)

* Republisher that subscribers to Amazon SQS and publishes domain event locally (forthcoming)

* Event sourced indexes, as persisted event source projections, to discover extant entity IDs (forthcoming)

* Ability to clear and rebuild a persisted event sourced projection (such as an index), by republishing
all events from the event store, with it as the only subscriber (forthcoming)

* Entity snapshots, to avoid replaying all events (forthcoming)

## Usage

Start by defining a domain entity. The entity's constructor
should accept the values it needs to initialize its variables.

In the example below, an Example entity inherits Created, Discarded,
and AttributeChanged events from its super class EventSourcedEntity.

```python
from eventsourcing.domain.model.entity import EventSourcedEntity

class Example(EventSourcedEntity):
    """
    An example event sourced domain model entity.
    """

    def __init__(self, a, b, **kwargs):
        super().__init__(**kwargs)
        self._a = a
        self._b = b

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, value):
        self._set_event_sourced_attribute_value(name='_a', value=value)

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        self._set_event_sourced_attribute_value(name='_b', value=value)

```

Next, define a factory method that returns new entity instances. Rather than directly constructing the entity object
instance, it should firstly instantiate a "created" domain event, and then call the mutator to obtain
an entity object instance. The factory method then publishes the event (for example, so that it might be
saved into the event store by the persistence subscriber) and returns the entity to the caller.

In the example below, the factory method is a module level function which firstly instantiates the
Example's Created domain event. The Example mutator is invoked, which returns an entity object instance when given a
Created event. The event is published, and the new domain entity is returned to the caller of the factory method.

```python
import uuid

def register_new_example(a, b):
    """
    Factory method for Example entities.
    """
    entity_id = uuid.uuid4().hex
    event = Example.Created(entity_id=entity_id, a=a, b=b)
    entity = Example.mutator(self=Example, event=event)
    publish(event=event)
    return entity
```

Next, define an event sourced repository class for your entity. Inherit from the base class
'EventSourcedRepository' and set the 'domain_class' attribute on the subclass.
In the example below, the ExampleRepository sets the Example class as its domain class.

```python
from eventsourcing.infrastructure.event_sourced_repo import EventSourcedRepository    

class ExampleRepository(EventSourcedRepository):    
    """
    Event sourced repository for the Example domain model entity.
    """
    domain_class = Example
```

Finally, define an application to have the event sourced repo and the factory method. Inheriting from
EventSourcedApplication means a persistence subscriber, an event store, and stored event persistence
will be set up when the application is instantiated.

In the example below, the ExampleApplication has an ExampleRepository, and for convenience the
'register_new_example' factory method described above (a module level function) is used to implement a
synonymous method on the application class.

```python
from eventsourcing.application.main import EventSourcedApplication

class ExampleApplication(EventSourcedApplication):
    """
    Example event sourced application.
    
    Has an Example repository, and a factory method for registering new examples.
    """

    def __init__(self):
        super().__init__()
        self.example_repo = ExampleRepository(event_store=self.event_store)

    def register_new_example(self, a, b):
        return register_new_example(a=a, b=b)
```

The event sourced application can be used as a context manager. Call the application's factory object to
register a new entity. Use the new entity's ID to retrieve the registered entity from the repository.

```python
with ExampleApplication() as app:
    
    # Register a new example.
    example1 = app.register_new_example(a=10, b=20)
    
    # Check the example is available in the repo.
    entity1 = app.example_repo[example1.id]
    assert entity1.a == 10
    assert entity1.b == 20
    
    # Change attribute values.
    entity1.a = 123
    
    # Check the new value is available in the repo.
    entity1 = app.example_repo[example1.id]
    assert entity1.a == 123
```

Congratulations! You have created a new event sourced application!
