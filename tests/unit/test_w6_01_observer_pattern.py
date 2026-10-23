from collections.abc import Generator

import pytest

from wocbots.agents import HOLLYWOOD_WEIGHTS, Agent
from wocbots.swarm.observer import BeeObserver
from wocbots.swarm.subject import BeeSubject

@pytest.fixture(scope="function")
def agent_under_test() -> Generator[Agent, None, None]:
    yield Agent(
            features=("f0",),
            eval_accuracy=0.5,
            eval_precision=0.5,
            eval_recall=0.5,
            confidence_weights=HOLLYWOOD_WEIGHTS,
        )

class SubjectClass(BeeSubject):
    def __init__(self, agent : Agent):
        super().__init__(agent=agent)

class ObserverClass(BeeObserver):
    def __init__(self, id : int = 0):
        super().__init__()
        self.counter = 0
        self.id = id

    def notify(self, presenter : Agent):
        self.counter += 1

def test_register(agent_under_test : Agent) -> None:
    subject = SubjectClass(agent=agent_under_test)
    observer = ObserverClass()
    subject.register_observer(bee_observer=observer)
    assert(observer in subject.observers)

def test_deregister(agent_under_test : Agent) -> None:
    subject = SubjectClass(agent=agent_under_test)
    observer = ObserverClass()
    subject.register_observer(bee_observer=observer)
    assert(observer in subject.observers)
    subject.deregister_observer(bee_observer=observer)
    assert(not (observer in subject.observers))

def test_multiple_registers(agent_under_test : Agent) -> None:
    subject = SubjectClass(agent=agent_under_test)
    observer1 = ObserverClass(id=1)
    observer2 = ObserverClass(id=2)
    observer4 = ObserverClass(id=4)
    observer8 = ObserverClass(id=8)

    subject.register_observer(observer1)
    subject.register_observer(observer2)
    subject.register_observer(observer4)
    subject.register_observer(observer8)

    assert(observer1 in subject.observers)
    assert(observer2 in subject.observers)
    assert(observer4 in subject.observers)
    assert(observer8 in subject.observers)

def test_deregister_from_multiple(agent_under_test : Agent) -> None:
    subject = SubjectClass(agent=agent_under_test)
    observer1 = ObserverClass(id=1)
    observer2 = ObserverClass(id=2)
    observer4 = ObserverClass(id=4)
    observer8 = ObserverClass(id=8)
    
    subject.register_observer(observer1)
    subject.register_observer(observer2)
    subject.register_observer(observer4)
    subject.register_observer(observer8)
    
    assert(observer1 in subject.observers)
    assert(observer2 in subject.observers)
    assert(observer4 in subject.observers)
    assert(observer8 in subject.observers)

    subject.deregister_observer(observer4)

    assert(observer1 in subject.observers)
    assert(observer2 in subject.observers)
    assert(not observer4 in subject.observers)
    assert(observer8 in subject.observers)

def test_deregister_multiple(agent_under_test : Agent) -> None:
    subject = SubjectClass(agent=agent_under_test)
    observer1 = ObserverClass(id=1)
    observer2 = ObserverClass(id=2)
    observer4 = ObserverClass(id=4)
    observer8 = ObserverClass(id=8)
    
    subject.register_observer(observer1)
    subject.register_observer(observer2)
    subject.register_observer(observer4)
    subject.register_observer(observer8)
    
    assert(observer1 in subject.observers)
    assert(observer2 in subject.observers)
    assert(observer4 in subject.observers)
    assert(observer8 in subject.observers)

    subject.deregister_observer(observer4)
    subject.deregister_observer(observer2)

    assert(observer1 in subject.observers)
    assert(not observer2 in subject.observers)
    assert(not observer4 in subject.observers)
    assert(observer8 in subject.observers)

def test_notify(agent_under_test : Agent) -> None:
    subject = SubjectClass(agent=agent_under_test)
    observer = ObserverClass()

    subject.register_observer(observer)
    subject.notify_observers()

    assert (observer.counter == 1)

def test_multiple_notifications(agent_under_test : Agent) -> None:
    subject = SubjectClass(agent=agent_under_test)
    observer = ObserverClass()
    
    subject.register_observer(observer)
    subject.notify_observers()
    subject.notify_observers()
    subject.notify_observers()
    
    assert (observer.counter == 3)