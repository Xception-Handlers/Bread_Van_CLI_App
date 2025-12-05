"""
Observer Pattern implementation for Bread Van App
This pattern allows Drivers (Subjects) to notify Residents (Observers) of events
"""


class Subject:
    """Driver acts as Subject - maintains list of observer Residents"""
    
    def __init__(self):
        # List of observers (Residents) subscribed to this Driver
        self._observers = []
    
    def attach(self, observer):
        """
        Add an observer to the notification list
        """
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        """
        Remove an observer from the notification list  
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, message):
        """
        Notify all subscribed observers with a message
        """
        for observer in self._observers:
            observer.update(message)


class Observer:
    """Resident acts as Observer - receives updates from Driver"""
    def update(self, message):
        pass  # To be implemented by Resident class