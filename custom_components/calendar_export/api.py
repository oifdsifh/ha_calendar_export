"""API for calendar export."""

from datetime import datetime, timedelta
from http import HTTPStatus

import hashlib
import pytz
from aiohttp import web
from homeassistant.components import http
from homeassistant.components.calendar import DOMAIN as CALENDAR_DOMAIN
from homeassistant.components.calendar import CalendarEntity
from homeassistant.components.todo import (
    DOMAIN as TODO_DOMAIN,
)
from homeassistant.components.todo import (
    TodoListEntity,
)
from icalendar import Calendar, Event, Todo


class CalendarExportAPI(http.HomeAssistantView):
    """View to export calendar in ICS format."""

    url = "/api/calendars/{entity_id}/export.ics"
    name = "api:calendars:ics"
    requires_auth = False

    async def get(self, request: web.Request, entity_id: str):  # noqa: ANN201
        """Handle GET requests to export calendar in ICS format."""
        hass = request.app[http.KEY_HASS]

        if not (
            entity := hass.data[CALENDAR_DOMAIN].get_entity(entity_id)
        ) or not isinstance(entity, CalendarEntity):
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        if not isinstance(entity, CalendarEntity):
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        # Generate ICS data
        cal = Calendar()
        cal["X-WR-CALNAME"] = entity.name
        cal["PRODID"] = "-//Home Assistant//Calendar Export//EN"

        tz = pytz.timezone(hass.config.time_zone)

        events = await entity.async_get_events(
            hass,
            datetime.now(tz=tz) - timedelta(days=365),
            datetime.now(tz=tz) + timedelta(days=365),
        )

        for event in events:
            e = Event()
            uid = hashlib.md5((event.start.ctime() + event.end.ctime() + event.summary).encode()).hexdigest()
            e.add("uid", event.uid or uid)
            e.add("summary", event.summary)
            e.add("dtstart", event.start)
            e.add("dtend", event.end)
            if event.description:
                e.add("description", event.description)
            if event.location:
                e.add("location", event.location)
            cal.add_component(e)

        ics = cal.to_ical().decode("utf-8")

        # Return ICS data as response
        return web.Response(
            status=HTTPStatus.OK,
            body=ics,
            headers={"Content-Type": "text/calendar"},
        )


class TodoListExportAPI(http.HomeAssistantView):
    """View to export todo list in ICS format."""

    url = "/api/todo/{entity_id}/export.ics"
    name = "api:todo:ics"
    requires_auth = False

    async def get(self, request: web.Request, entity_id: str):  # noqa: ANN201
        """Handle GET requests to export todo list in ICS format."""
        hass = request.app[http.KEY_HASS]

        if not (entity := hass.data[TODO_DOMAIN].get_entity(entity_id)):
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        if not isinstance(entity, TodoListEntity):
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        # Generate ICS data
        todo = Calendar()
        todo["X-WR-CALNAME"] = entity.name
        todo["PRODID"] = "-//Home Assistant//Todo List Export//EN"

        todos = entity.todo_items

        if todos:
            for todo_item in todos:
                t = Todo()
                t.add("uid", todo_item.uid)
                t.add("summary", todo_item.summary)
                if todo_item.due:
                    t.add("due", todo_item.due)
                if todo_item.description:
                    t.add("description", todo_item.description)
                if todo_item.status:
                    t.add("status", todo_item.status.value)
                todo.add_component(t)

        ics = todo.to_ical().decode("utf-8")

        # Return ICS data as response
        return web.Response(
            status=HTTPStatus.OK,
            body=ics,
            headers={"Content-Type": "text/calendar"},
        )


class TodoListExportEventsAPI(http.HomeAssistantView):
    """View to export todo list in ICS format (using vevent not vtodo)."""

    url = "/api/todo/{entity_id}/export_events.ics"
    name = "api:todo:events_ics"
    requires_auth = False

    async def get(self, request: web.Request, entity_id: str):  # noqa: ANN201
        """Handle GET requests to export todo list in ICS format."""
        hass = request.app[http.KEY_HASS]

        if not (entity := hass.data[TODO_DOMAIN].get_entity(entity_id)):
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        if not isinstance(entity, TodoListEntity):
            return web.Response(status=HTTPStatus.BAD_REQUEST)

        # Generate ICS data
        todo = Calendar()
        todo["X-WR-CALNAME"] = entity.name
        todo["PRODID"] = "-//Home Assistant//Todo List Export Events//EN"

        todos = entity.todo_items

        if todos:
            for todo_item in todos:
                t = Event()
                t.add("uid", todo_item.uid)
                t.add("summary", todo_item.summary)
                if todo_item.due:
                    t.add("dtstart", todo_item.due)
                if todo_item.due:
                    t.add("dtend", todo_item.due)
                if todo_item.description:
                    t.add("description", todo_item.description)
                if todo_item.status:
                    t.add("status", todo_item.status.value)
                todo.add_component(t)

        ics = todo.to_ical().decode("utf-8")

        # Return ICS data as response
        return web.Response(
            status=HTTPStatus.OK,
            body=ics,
            headers={"Content-Type": "text/calendar"},
        )
