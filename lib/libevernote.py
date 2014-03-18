from dateutil.relativedelta import relativedelta
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import NoteSortOrder
from evernote.api.client import EvernoteClient
import settings


def get_notes(forDate, token):
    searchDateLowerLimit = forDate.strftime("%Y%m%d")
    searchDateUpperLimit = (forDate + relativedelta(days=+1)).strftime("%Y%m%d")

    foundNotes = _find_evernote_notes("created:{} -created:{}".format(searchDateLowerLimit, searchDateUpperLimit), token)

    notes = []
    for note in foundNotes:
        notes.append((note.guid, note.title.decode('UTF-8')))

    return notes


def _get_evernote_note_store(token):
    client = EvernoteClient(token=token, sandbox=False)
    return client.get_note_store()


def _find_evernote_notes(words, token):
    noteStore = _get_evernote_note_store(token)
    filter = NoteFilter(words=words, order=NoteSortOrder.CREATED)
    spec = NotesMetadataResultSpec(includeTitle=True)

    noteMetadata = noteStore.findNotesMetadata(token, filter, 0, 50, spec)

    return noteMetadata.notes