#!/usr/bin/env python3
"""
Emergency Knowledge Archive - Unified Interface Server

One command to access all of humanity's collected knowledge.

Usage:
    python START_ARCHIVE.py

Then open http://localhost:9000 in your browser.

Requirements:
    Python 3.7+ (no external packages required - uses only standard library)
"""

import http.server
import socketserver
import json
import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal
import mimetypes
import urllib.parse
import urllib.request
from pathlib import Path
from functools import partial
import socket

# =============================================================================
# CONFIGURATION
# =============================================================================

PORT = 9000
KIWIX_PORT = 8080
LLAMAFILE_PORT = 8081

ARCHIVE_ROOT = Path(__file__).parent.resolve()

DIRS = {
    'kiwix_data': ARCHIVE_ROOT / 'kiwix' / 'data',
    'kiwix_tools': ARCHIVE_ROOT / 'kiwix' / 'tools',
    'llm': ARCHIVE_ROOT / 'llm',
    'medical': ARCHIVE_ROOT / 'medical',
    'survival': ARCHIVE_ROOT / 'survival',
    'library': ARCHIVE_ROOT / 'library',
    'art': ARCHIVE_ROOT / 'art',
    'met_art': ARCHIVE_ROOT / 'met_art',
    'sheet_music': ARCHIVE_ROOT / 'sheet_music',
    'skills_videos': ARCHIVE_ROOT / 'skills_videos',
    'maps': ARCHIVE_ROOT / 'maps',
}

# Composer name normalization
COMPOSER_MAP = {
    # Mutopia short codes -> proper names
    'BachJS': 'Bach, Johann Sebastian',
    'BachCPE': 'Bach, Carl Philipp Emanuel',
    'BeethovenLv': 'Beethoven, Ludwig van',
    'BrahmsJ': 'Brahms, Johannes',
    'ChopinFF': 'Chopin, Frederic',
    'DebussyC': 'Debussy, Claude',
    'DvorakA': 'Dvorak, Antonin',
    'FaureG': 'Faure, Gabriel',
    'FranckC': 'Franck, Cesar',
    'GriegE': 'Grieg, Edvard',
    'HandelGF': 'Handel, George Frideric',
    'HaydnFJ': 'Haydn, Franz Joseph',
    'HaydnJM': 'Haydn, Johann Michael',
    'LisztF': 'Liszt, Franz',
    'MozartWA': 'Mozart, Wolfgang Amadeus',
    'MendelssohnF': 'Mendelssohn, Felix',
    'Mendelssohn-BartholdyF': 'Mendelssohn, Felix',
    'RachmaninoffS': 'Rachmaninoff, Sergei',
    'SchumannR': 'Schumann, Robert',
    'SchubertF': 'Schubert, Franz',
    'TchaikovskyPI': 'Tchaikovsky, Pyotr Ilyich',
    'VivaldiA': 'Vivaldi, Antonio',
    'VerdiG': 'Verdi, Giuseppe',
    'SatieE': 'Satie, Erik',
    'BartokB': 'Bartok, Bela',
    'PurcellH': 'Purcell, Henry',
    'TelemannGP': 'Telemann, Georg Philipp',
    'PachelbelJ': 'Pachelbel, Johann',
    'ScarlattiD': 'Scarlatti, Domenico',
    'PaganiniN': 'Paganini, Niccolo',
    'SorF': 'Sor, Fernando',
    'CarcassiM': 'Carcassi, Matteo',
    'CarulliF': 'Carulli, Ferdinando',
    'GiulianiM': 'Giuliani, Mauro',
    'TarregaF': 'Tarrega, Francisco',
    'CzernyC': 'Czerny, Carl',
    'ClementiM': 'Clementi, Muzio',
    'BurgmullerJFF': 'Burgmuller, Johann Friedrich Franz',
    'JoplinS': 'Joplin, Scott',
    'DowlandJ': 'Dowland, John',
    'SousaJP': 'Sousa, John Philip',
    'GottschalkLM': 'Gottschalk, Louis Moreau',
    'GounodC': 'Gounod, Charles',
    'KuhlauF': 'Kuhlau, Friedrich',
    'LullyJB': 'Lully, Jean-Baptiste',
    'MonteverdiC': 'Monteverdi, Claudio',
    'MorleyT': 'Morley, Thomas',
    'FosterSC': 'Foster, Stephen Collins',
    'HolstGT': 'Holst, Gustav',
    'RameauJP': 'Rameau, Jean-Philippe',
    'BuxtehudeD': 'Buxtehude, Dietrich',
    'QuantzJJ': 'Quantz, Johann Joachim',
    'SpohrL': 'Spohr, Louis',
    'ScriabinA': 'Scriabin, Alexander',
    'SullivanA': 'Sullivan, Arthur',
    'TallisT': 'Tallis, Thomas',
    'WeelkesT': 'Weekes, Thomas',
    'GalileiV': 'Galilei, Vincenzo',
    'GesualdoC': 'Gesualdo, Carlo',
    'PorporaN': 'Porpora, Nicola',
    'FrobergerJJ': 'Froberger, Johann Jacob',
    'HumperdinckE': 'Humperdinck, Engelbert',
    'BruchM': 'Bruch, Max',
    'BrucknerA': 'Bruckner, Anton',
    'AlbenizIMF': 'Albeniz, Isaac',
    'AlkanCV': 'Alkan, Charles-Valentin',
    'MarenzioL': 'Marenzio, Luca',
    'VictoriaTLd': 'Victoria, Tomas Luis de',
    'MarcelloB': 'Marcello, Benedetto',
    'SanzG': 'Sanz, Gaspar',
    'MertzJK': 'Mertz, Johann Kaspar',
    'RegerM': 'Reger, Max',
    'DussekJL': 'Dussek, Jan Ladislav',
    'FieldJ': 'Field, John',
    'DevienneF': 'Devienne, Francois',
    'StraussJJ': 'Strauss, Johann II',
    'Rimsky-KorsakovN': 'Rimsky-Korsakov, Nikolai',
    'Saint-SaensC': 'Saint-Saens, Camille',
    'BoismortierJBd': 'Boismortier, Joseph Bodin de',
    'LottiA': 'Lotti, Antonio',
    'MartiniGB': 'Martini, Giovanni Battista',
    # IA identifiers
    'Beethoven': 'Beethoven, Ludwig van',
    # IMSLP with diacritics -> merge with normalized
    'Bartók, Béla': 'Bartok, Bela',
    'Chopin, Frédéric': 'Chopin, Frederic',
    'Dvořák, Antonín': 'Dvorak, Antonin',
    'Fauré, Gabriel': 'Faure, Gabriel',
    'Saint-Saëns, Camille': 'Saint-Saens, Camille',
    'Hanon, Charles-Louis': 'Hanon, Charles-Louis',
}

import re

def normalize_composer(name):
    """Normalize a composer name to 'Last, First' format."""
    if name in COMPOSER_MAP:
        return COMPOSER_MAP[name]
    # Already in "Last, First" format
    if ',' in name:
        return name
    # Try to split CamelCase Mutopia-style: "AguadoD" -> "Aguado, D."
    # Pattern: uppercase letters mark boundaries, last chunk is initials
    m = re.match(r'^([A-Z][a-z]+(?:[A-Z][a-z]+)*)([A-Z]+)$', name)
    if m:
        last = m.group(1)
        # Split internal CamelCase in last name: "StanchinskyAV" shouldn't split
        # But "HulakArtemovskyS" should stay as-is
        initials = m.group(2)
        return f"{last}, {'. '.join(initials)}."
    return name

processes = []

# Word index for fuzzy search suggestions
WORD_INDEX = set()
MUSIC_TEXT_INDEX = {}
MEDICAL_INDEX = []  # Cached in memory for RAG
GUTENBERG_CATALOG = []  # [{title, author, id, shelf}, ...]
GUTENBERG_ID_MAP = {}   # {gutenberg_id: title}
GUTENBERG_ZIM_NAME = None  # e.g. "gutenberg_en_all_2025-11"
GUTENBERG_CONTENT_CACHE = {}  # LRU-ish cache for cleaned book HTML
GUTENBERG_CACHE_MAX = 50

def load_music_text_index():
    """Load the music PDF text index for full-text music search."""
    global MUSIC_TEXT_INDEX
    index_path = ARCHIVE_ROOT / 'music_text_index.json'
    if not index_path.exists():
        return
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            MUSIC_TEXT_INDEX = json.load(f)
        print(f"  Music text index: {len(MUSIC_TEXT_INDEX)} PDFs with text")
    except Exception as e:
        print(f"  Music text index failed: {e}")

def build_word_index():
    """Build a set of unique words from the medical index for spelling suggestions. Also cache the index for RAG."""
    global WORD_INDEX, MEDICAL_INDEX
    index_path = ARCHIVE_ROOT / 'medical_index.json'
    if not index_path.exists():
        return
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            MEDICAL_INDEX = json.load(f)
        words = set()
        for doc in MEDICAL_INDEX:
            for page in doc.get('pages', []):
                for w in re.findall(r'[a-zA-Z]{4,}', page.get('text', '')):
                    words.add(w.lower())
        WORD_INDEX = words
        print(f"  Word index: {len(WORD_INDEX)} unique terms")
    except Exception as e:
        print(f"  Word index failed: {e}")


def detect_gutenberg_zim():
    """Detect the Gutenberg ZIM content name from Kiwix's OPDS catalog."""
    global GUTENBERG_ZIM_NAME
    try:
        url = f'http://localhost:{KIWIX_PORT}/catalog/v2/entries'
        req = urllib.request.Request(url, headers={'User-Agent': 'Archive/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml = resp.read().decode('utf-8', errors='replace')
        # Find gutenberg entry and extract content path
        for m in re.finditer(r'<name>(gutenberg[^<]*)</name>', xml):
            name = m.group(1)
            # Find the corresponding text/html link
            chunk = xml[m.end():m.end() + 500]
            link_m = re.search(r'href="/content/([^"]+)"', chunk)
            if link_m:
                GUTENBERG_ZIM_NAME = link_m.group(1)
                print(f"  Gutenberg ZIM: {GUTENBERG_ZIM_NAME}")
                return
    except Exception as e:
        print(f"  Gutenberg ZIM detection failed: {e}")


def load_gutenberg_catalog():
    """Load the full Gutenberg book catalog from Kiwix."""
    global GUTENBERG_CATALOG, GUTENBERG_ID_MAP
    if not GUTENBERG_ZIM_NAME:
        return
    try:
        url = f'http://localhost:{KIWIX_PORT}/content/{GUTENBERG_ZIM_NAME}/full_by_popularity.js'
        req = urllib.request.Request(url, headers={'User-Agent': 'Archive/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode('utf-8', errors='replace')
        # Parse: var json_data = [[title, author, pop, id, shelf], ...]
        arr_str = data.split('var json_data = ', 1)[1]
        depth = 0
        end = 0
        for i, c in enumerate(arr_str):
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
            if depth == 0:
                end = i + 1
                break
        raw = json.loads(arr_str[:end])
        catalog = []
        id_map = {}
        for item in raw:
            entry = {
                'title': item[0],
                'author': item[1],
                'id': item[3],
                'shelf': item[4] if len(item) > 4 else '',
            }
            catalog.append(entry)
            id_map[item[3]] = item[0]
        GUTENBERG_CATALOG = catalog
        GUTENBERG_ID_MAP = id_map
        print(f"  Gutenberg catalog: {len(catalog)} books")
    except Exception as e:
        print(f"  Gutenberg catalog failed: {e}")


def get_gutenberg_content(book_id):
    """Fetch and clean a Gutenberg book's HTML from Kiwix."""
    if book_id in GUTENBERG_CONTENT_CACHE:
        return GUTENBERG_CONTENT_CACHE[book_id]
    if not GUTENBERG_ZIM_NAME or book_id not in GUTENBERG_ID_MAP:
        return None
    title = GUTENBERG_ID_MAP[book_id]
    encoded_title = urllib.parse.quote(title)
    url = f'http://localhost:{KIWIX_PORT}/content/{GUTENBERG_ZIM_NAME}/{encoded_title}.{book_id}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Archive/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None

    # Extract body content
    body_match = re.search(r'<body[^>]*>(.*)</body>', html, re.DOTALL)
    if not body_match:
        return None
    body = body_match.group(1)

    # Remove ZIM overlay elements
    body = re.sub(r'<span class="zim_info">.*?</span>', '', body, flags=re.DOTALL)
    body = re.sub(r'<span class="zim_epub">.*?</span>', '', body, flags=re.DOTALL)
    body = re.sub(r'<span class="zim_up"[^>]*>.*?</span>', '', body, flags=re.DOTALL)
    body = re.sub(r'<link[^>]*font-awesome[^>]*/>', '', body, flags=re.DOTALL)

    # Remove PG header and footer if present
    body = re.sub(r'<div[^>]*id="pg-header"[^>]*>.*?</div>\s*', '', body, flags=re.DOTALL)
    body = re.sub(r'<div[^>]*id="pg-footer"[^>]*>.*?</div>\s*', '', body, flags=re.DOTALL)

    # Rewrite relative image URLs
    img_base = f'http://localhost:{KIWIX_PORT}/content/{GUTENBERG_ZIM_NAME}/'
    body = re.sub(r'src="(?!http)([^"]+)"', lambda m: f'src="{img_base}{urllib.parse.quote(m.group(1))}"', body)

    # Strip leading empty divs
    body = re.sub(r'^(\s*<div>\s*</div>\s*)+', '', body)

    result = {'title': title, 'html': body}

    # Cache with eviction
    if len(GUTENBERG_CONTENT_CACHE) >= GUTENBERG_CACHE_MAX:
        oldest = next(iter(GUTENBERG_CONTENT_CACHE))
        del GUTENBERG_CONTENT_CACHE[oldest]
    GUTENBERG_CONTENT_CACHE[book_id] = result
    return result


def rag_retrieve(query, max_passages=4, max_chars=2500):
    """Retrieve relevant passages from the library index for RAG context."""
    if not MEDICAL_INDEX or not query:
        return ""
    query_lower = query.lower()
    # Extract key terms (skip very short words)
    terms = [w for w in query_lower.split() if len(w) >= 3]
    if not terms:
        return ""

    scored = []
    for doc in MEDICAL_INDEX:
        for page in doc.get('pages', []):
            text = page.get('text', '')
            text_lower = text.lower()
            # Score by number of query terms found
            hits = sum(1 for t in terms if t in text_lower)
            if hits > 0:
                scored.append((hits, doc['title'], doc['category'], page['page'], text, doc['id']))

    # Sort by relevance (most terms matched)
    scored.sort(key=lambda x: -x[0])

    # Build context string within char budget
    passages = []
    total = 0
    seen_docs = set()
    for hits, title, category, page_num, text, doc_id in scored[:max_passages * 2]:
        # Trim long passages to ~800 chars around the best match
        snippet = text
        if len(snippet) > 800:
            # Find best position
            best_pos = 0
            for t in terms:
                pos = text.lower().find(t)
                if pos >= 0:
                    best_pos = pos
                    break
            start = max(0, best_pos - 400)
            end = min(len(text), best_pos + 400)
            snippet = ('...' if start > 0 else '') + text[start:end] + ('...' if end < len(text) else '')

        entry = f"[{category.upper()} - {title}, p{page_num} | ref:{doc_id}]\n{snippet}"
        if total + len(entry) > max_chars:
            break
        passages.append(entry)
        total += len(entry)
        if len(passages) >= max_passages:
            break

    return '\n\n'.join(passages)

# =============================================================================
# EMERGENCY KNOWLEDGE BASE
# =============================================================================

def load_emergency_knowledge():
    """Load the emergency knowledge file if it exists."""
    knowledge_file = ARCHIVE_ROOT / 'EMERGENCY_KNOWLEDGE.txt'
    if not knowledge_file.exists():
        knowledge_file = ARCHIVE_ROOT / 'Emergency knowledge.txt'
    if knowledge_file.exists():
        try:
            return knowledge_file.read_text(encoding='utf-8')
        except Exception:
            pass
    return ""

EMERGENCY_KNOWLEDGE = load_emergency_knowledge()

# =============================================================================
# HTML TEMPLATE - Clean, minimal, light design
# =============================================================================

def load_html_template():
    """Load the HTML template from template.html, falling back to inline minimal version."""
    template_path = ARCHIVE_ROOT / 'template.html'
    if template_path.exists():
        try:
            return template_path.read_text(encoding='utf-8')
        except Exception:
            pass
    # Minimal fallback if template.html is missing
    return '''<!DOCTYPE html>
<html><head><title>Knowledge Archive</title></head>
<body style="font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 20px;">
<h1>Knowledge Archive</h1>
<p>The template.html file is missing. Please ensure it is in the same directory as START_ARCHIVE.py.</p>
<p>Available services:</p>
<ul>
<li><a href="http://localhost:8080">Kiwix (Wikipedia, Books, etc.)</a></li>
</ul>
</body></html>'''

MAIN_HTML = load_html_template()

# =============================================================================
# HTTP SERVER
# =============================================================================

class ArchiveHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, archive_root=None, **kwargs):
        self.archive_root = archive_root or ARCHIVE_ROOT
        super().__init__(*args, directory=str(self.archive_root), **kwargs)
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/chat':
            self.handle_chat()
            return
        self.send_error(404)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        
        if path == '/' or path == '/index.html':
            self.send_html(MAIN_HTML)
            return
        
        if path.startswith('/api/'):
            self.handle_api(path, query)
            return
        
        if path.startswith('/files/'):
            self.serve_file(path[7:])
            return
        
        super().do_GET()
    
    def handle_api(self, path, query):
        if path == '/api/files/medical':
            self.send_json(self.list_files(DIRS['medical']))
        elif path == '/api/files/survival':
            self.send_json(self.list_files(DIRS['survival']))
        elif path == '/api/files/videos':
            self.send_json(self.list_videos())
        elif path == '/api/files/music':
            self.send_json(self.list_all_music())
        elif path == '/api/files/library':
            self.send_json(self.list_library_files())
        elif path == '/api/files/maps':
            # Include both PMTiles and osm-data files
            files = self.list_files(DIRS['maps'], recursive=False)
            files += self.list_files(DIRS['maps'] / 'osm-data', recursive=False)
            self.send_json(files)
        elif path == '/api/chat':
            self.handle_chat()
            return
        elif path == '/api/kiwix/search':
            q = query.get('q', [''])[0]
            self.send_json(self.search_kiwix(q))
        elif path == '/api/emergency':
            self.send_text(EMERGENCY_KNOWLEDGE)
        elif path == '/api/music/search':
            q = query.get('q', [''])[0]
            self.send_json(self.search_music(q))
        elif path == '/api/art/metadata':
            self.serve_art_metadata()
        elif path == '/api/medical/index':
            self.serve_medical_index()
        elif path == '/api/medical/search':
            q = query.get('q', [''])[0]
            cat = query.get('category', [None])[0]
            self.send_json(self.search_medical(q, cat))
        elif path == '/api/search':
            q = query.get('q', [''])[0]
            self.send_json(self.search_files(q))
        elif path == '/api/gutenberg/catalog':
            self.send_json(GUTENBERG_CATALOG)
        elif path.startswith('/api/gutenberg/content/'):
            try:
                book_id = int(path.split('/')[-1])
            except ValueError:
                self.send_error(400)
                return
            result = get_gutenberg_content(book_id)
            if result:
                self.send_json(result)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def handle_chat(self):
        """Handle chat with RAG: retrieve relevant passages, send to LLM, stream response."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            messages = data.get('messages', [])

            if not messages:
                self.send_json({'error': 'No messages'})
                return

            # Get the latest user message for RAG retrieval
            last_user_msg = ''
            for m in reversed(messages):
                if m.get('role') == 'user':
                    last_user_msg = m.get('content', '')
                    break

            # Retrieve relevant context
            context = rag_retrieve(last_user_msg)

            # Build system prompt -- keep it concise to save context for RAG
            system = "You are a helpful assistant for an offline knowledge archive containing medical guides, survival manuals, and homesteading references. Be direct, practical, and concise. Keep answers short -- use numbered steps for procedures. Do not use markdown headers (no # or ##). Use plain text with bold (**word**) for emphasis only."
            if context:
                system += "\n\nREFERENCE MATERIAL:\n\n" + context
                system += "\n\nUse the reference material to answer. Cite the source briefly. If the material doesn't cover it, say so."

            # Build messages for LLM
            llm_messages = [{'role': 'system', 'content': system}]
            # Keep last 10 messages for conversation history
            for m in messages[-10:]:
                llm_messages.append({'role': m['role'], 'content': m['content']})

            # Stream from LLM
            llm_url = f'http://localhost:{LLAMAFILE_PORT}/v1/chat/completions'
            llm_body = json.dumps({
                'model': 'local',
                'messages': llm_messages,
                'stream': True,
                'temperature': 0.3,
                'max_tokens': 512,
            }).encode('utf-8')

            req = urllib.request.Request(llm_url, data=llm_body, method='POST',
                                         headers={'Content-Type': 'application/json'})

            # Stream response back to client
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    line = line.decode('utf-8', errors='replace').strip()
                    if line.startswith('data: '):
                        self.wfile.write((line + '\n\n').encode('utf-8'))
                        self.wfile.flush()

            self.wfile.write(b'data: [DONE]\n\n')
            self.wfile.flush()

        except Exception as e:
            try:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'AI unavailable: {str(e)}'}).encode('utf-8'))
            except Exception:
                pass

    def search_kiwix(self, query):
        """Proxy search to Kiwix and parse results."""
        if not query:
            return []
        try:
            url = f'http://localhost:{KIWIX_PORT}/search?pattern={urllib.parse.quote(query)}&pageLength=8'
            req = urllib.request.Request(url, headers={'User-Agent': 'Archive/1.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            # Parse href="/content/BOOK/ARTICLE" links
            results = []
            seen = set()
            for m in re.finditer(r'href="(/content/([^/]+)/([^"]+))"', html):
                path, book, article = m.group(1), m.group(2), m.group(3)
                title = urllib.parse.unquote(article).replace('_', ' ')
                if title in seen:
                    continue
                seen.add(title)
                # Identify source
                if 'wikipedia' in book:
                    source = 'Wikipedia'
                elif 'gutenberg' in book:
                    source = 'Gutenberg'
                elif 'stackoverflow' in book:
                    source = 'Stack Overflow'
                elif 'wikibooks' in book:
                    source = 'WikiBooks'
                elif 'medicine' in book:
                    source = 'WikiMed'
                else:
                    source = book
                results.append({
                    'title': title,
                    'url': f'http://localhost:{KIWIX_PORT}{path}',
                    'source': source,
                })
            return results
        except Exception:
            return []

    def search_music(self, query):
        """Search music by PDF text content + metadata."""
        if not query:
            return []
        query_lower = query.lower()
        results = []
        # Search text index
        for path, text in MUSIC_TEXT_INDEX.items():
            if query_lower in text.lower():
                # Extract snippet
                idx = text.lower().find(query_lower)
                start = max(0, idx - 60)
                end = min(len(text), idx + len(query) + 60)
                snippet = ('...' if start > 0 else '') + text[start:end].strip() + ('...' if end < len(text) else '')
                # Derive name from path
                p = Path(path)
                name = p.stem.replace('_', ' ').replace('-', ' ')
                results.append({
                    'path': path,
                    'name': name,
                    'snippet': snippet,
                })
                if len(results) >= 50:
                    break
        return results

    def serve_art_metadata(self):
        meta_path = DIRS['met_art'] / 'metadata.json'
        if meta_path.exists():
            self.serve_file(str(meta_path.relative_to(self.archive_root)))
        else:
            self.send_json([])

    def serve_medical_index(self):
        index_path = ARCHIVE_ROOT / 'medical_index.json'
        if index_path.exists():
            self.serve_file('medical_index.json')
        else:
            self.send_json([])

    def search_medical(self, query, category_filter=None):
        if not query:
            return {'results': [], 'suggestions': []}
        if not MEDICAL_INDEX:
            return {'results': [], 'suggestions': []}
        try:
            index = MEDICAL_INDEX
            query_lower = query.lower()
            results = []
            for doc in index:
                if category_filter and doc.get('category') != category_filter:
                    continue
                for page in doc.get('pages', []):
                    if query_lower in page.get('text', '').lower():
                        text = page['text']
                        idx = text.lower().find(query_lower)
                        start = max(0, idx - 80)
                        end = min(len(text), idx + len(query) + 80)
                        snippet = ('...' if start > 0 else '') + text[start:end].strip() + ('...' if end < len(text) else '')
                        results.append({
                            'doc_id': doc['id'],
                            'title': doc['title'],
                            'category': doc['category'],
                            'page': page['page'],
                            'snippet': snippet
                        })
                        if len(results) >= 50:
                            return {'results': results, 'suggestions': []}

            # If no results, suggest corrections
            suggestions = []
            if not results and WORD_INDEX and len(query_lower) >= 3:
                import difflib
                matches = difflib.get_close_matches(query_lower, WORD_INDEX, n=5, cutoff=0.6)
                suggestions = matches

            return {'results': results, 'suggestions': suggestions}
        except Exception:
            return {'results': [], 'suggestions': []}
    
    def list_files(self, directory, recursive=True):
        files = []
        directory = Path(directory)
        if not directory.exists():
            return files
        
        pattern = '**/*' if recursive else '*'
        for path in directory.glob(pattern):
            if path.is_file() and not path.name.startswith('.'):
                files.append({
                    'name': path.name,
                    'path': str(path.relative_to(self.archive_root)),
                    'size': path.stat().st_size
                })
        return sorted(files, key=lambda x: x['name'].lower())
    
    def list_library_files(self):
        """List all library PDFs across medical, survival, and library directories."""
        files = []
        sources = [
            ('Medical', DIRS['medical']),
            ('Survival', DIRS['survival']),
        ]
        # Add library subdirectories as categories
        lib_dir = DIRS['library']
        if lib_dir.exists():
            for sub in sorted(lib_dir.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.'):
                    cat = sub.name.replace('-', ' ').replace('_', ' ').title()
                    sources.append((cat, sub))

        for category, directory in sources:
            if not directory.exists():
                continue
            for path in directory.rglob('*'):
                if path.is_file() and path.suffix.lower() == '.pdf' and not path.name.startswith('.'):
                    name = path.stem.replace('_', ' ').replace('-', ' ')
                    # Clean up common IA naming artifacts
                    if any(name.lower().endswith(s) for s in (' text', ' encrypted')):
                        continue
                    files.append({
                        'name': name,
                        'path': str(path.relative_to(self.archive_root)),
                        'size': path.stat().st_size,
                        'category': category,
                    })
        return sorted(files, key=lambda x: (x['category'].lower(), x['name'].lower()))

    def list_all_music(self):
        files = []
        sheet_root = DIRS['sheet_music']

        # Mutopia rendered PDFs (Composer/Work/file.pdf)
        pdf_dir = sheet_root / 'pdf'
        if pdf_dir.exists():
            for pdf in pdf_dir.rglob('*.pdf'):
                rel = pdf.relative_to(pdf_dir)
                parts = rel.parts
                files.append({
                    'name': pdf.stem.replace('_', ' ').replace('-', ' '),
                    'path': str(pdf.relative_to(self.archive_root)),
                    'size': pdf.stat().st_size,
                    'composer': parts[0] if len(parts) >= 1 else 'Unknown',
                    'work': parts[1] if len(parts) >= 2 else '',
                    'source': 'Mutopia',
                })

        # IMSLP scores (Composer/Work/file.pdf)
        imslp_dir = sheet_root / 'imslp'
        if imslp_dir.exists():
            for pdf in imslp_dir.rglob('*.pdf'):
                rel = pdf.relative_to(imslp_dir)
                parts = rel.parts
                files.append({
                    'name': parts[1] if len(parts) >= 2 else pdf.stem,
                    'path': str(pdf.relative_to(self.archive_root)),
                    'size': pdf.stat().st_size,
                    'composer': parts[0] if len(parts) >= 1 else 'Unknown',
                    'work': parts[1] if len(parts) >= 2 else '',
                    'source': 'IMSLP',
                })

        # Bach-Gesellschaft (volume PDFs)
        bga_dir = sheet_root / 'bach-gesellschaft' / 'bach-gesellschaft-ausgabe'
        if bga_dir.exists():
            for pdf in bga_dir.glob('*.pdf'):
                if '_text' in pdf.name:
                    continue  # skip OCR text PDFs
                files.append({
                    'name': pdf.stem.replace('_', ' '),
                    'path': str(pdf.relative_to(self.archive_root)),
                    'size': pdf.stat().st_size,
                    'composer': 'Bach, Johann Sebastian',
                    'work': 'Bach-Gesellschaft Ausgabe',
                    'source': 'Internet Archive',
                })

        # Other Internet Archive scores
        IA_NAME_MAP = {
            'beethovensmaster05beet': 'Complete Piano Sonatas (Breitkopf)',
            'completepianocon0000beet': 'Complete Piano Concertos (Breitkopf)',
            'completepianocon0000beet_encrypted': 'Complete Piano Concertos (Breitkopf)',
            'completesonatasv0000beet': 'Complete Cello Sonatas (Breitkopf)',
            'completesonatasv0000beet_encrypted': 'Complete Cello Sonatas (Breitkopf)',
        }
        ia_dir = sheet_root / 'ia-scores'
        if ia_dir.exists():
            for pdf in ia_dir.glob('*.pdf'):
                stem = pdf.stem
                name = IA_NAME_MAP.get(stem, stem.replace('_', ' ').replace('-', ' '))
                composer = 'Beethoven, Ludwig van' if 'beethoven' in stem.lower() or 'beet' in stem.lower() else 'Various'
                files.append({
                    'name': name,
                    'path': str(pdf.relative_to(self.archive_root)),
                    'size': pdf.stat().st_size,
                    'composer': composer,
                    'work': '',
                    'source': 'Internet Archive',
                })

        # Normalize all composer names
        for f in files:
            f['composer'] = normalize_composer(f['composer'])
        return sorted(files, key=lambda x: (x['composer'].lower(), x['name'].lower()))

    def list_videos(self):
        videos = []
        video_dir = DIRS['skills_videos']
        if not video_dir.exists():
            return videos
        
        video_extensions = {'.mp4', '.webm', '.mkv', '.avi', '.mov'}
        for category_dir in video_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                category_name = category_dir.name.replace('_', ' ').title()
                for video_file in category_dir.iterdir():
                    if video_file.suffix.lower() in video_extensions:
                        videos.append({
                            'name': video_file.stem,
                            'path': str(video_file.relative_to(self.archive_root)),
                            'size': video_file.stat().st_size,
                            'category': category_name
                        })
        return sorted(videos, key=lambda x: (x['category'], x['name'].lower()))
    
    def search_files(self, query):
        if not query:
            return []
        results = []
        query_lower = query.lower()
        
        for category, directory in [('medical', DIRS['medical']), ('survival', DIRS['survival']), 
                                     ('art', DIRS['art']), ('sheet_music', DIRS['sheet_music']),
                                     ('skills_videos', DIRS['skills_videos'])]:
            if not directory.exists():
                continue
            for path in directory.rglob('*'):
                if path.is_file() and query_lower in path.name.lower():
                    results.append({
                        'name': path.name,
                        'path': str(path.relative_to(self.archive_root)),
                        'category': category.replace('_', ' ').title()
                    })
        return results[:50]
    
    def serve_file(self, file_path):
        # Decode URL-encoded characters (e.g., %20 -> space)
        file_path = urllib.parse.unquote(file_path)
        full_path = self.archive_root / file_path
        if not full_path.exists() or not full_path.is_file():
            self.send_error(404)
            return

        try:
            full_path.resolve().relative_to(self.archive_root.resolve())
        except ValueError:
            self.send_error(403)
            return

        mime_type, _ = mimetypes.guess_type(str(full_path))
        if not mime_type:
            mime_type = 'application/octet-stream'
        if full_path.suffix == '.pmtiles':
            mime_type = 'application/octet-stream'

        file_size = full_path.stat().st_size

        # Handle Range requests (needed for PMTiles)
        range_header = self.headers.get('Range')
        if range_header and range_header.startswith('bytes='):
            try:
                range_spec = range_header[6:]
                start_str, end_str = range_spec.split('-', 1)
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                with open(full_path, 'rb') as f:
                    f.seek(start)
                    content = f.read(length)

                self.send_response(206)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Length', length)
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
                return
            except (ValueError, IndexError):
                pass

        try:
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', file_size)
            self.send_header('Accept-Ranges', 'bytes')
            # Force PDFs to display inline in browser instead of downloading
            if mime_type == 'application/pdf':
                self.send_header('Content-Disposition', f'inline; filename="{full_path.name}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open(full_path, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_html(self, content):
        encoded = content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)
    
    def send_json(self, data):
        content = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
    
    def send_text(self, text):
        encoded = text.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)
    
    def log_message(self, format, *args):
        pass


# =============================================================================
# SERVICE MANAGEMENT
# =============================================================================

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0


def find_kiwix_serve():
    kiwix_tools = DIRS['kiwix_tools']
    if not kiwix_tools.exists():
        return None
    
    if sys.platform == 'win32':
        patterns = ['**/kiwix-serve.exe', 'kiwix-serve.exe']
    else:
        patterns = ['**/kiwix-serve', 'kiwix-serve']
    
    for pattern in patterns:
        for path in kiwix_tools.glob(pattern):
            if path.is_file():
                return path
    return None


def find_llamafile():
    llm_dir = DIRS['llm']
    if not llm_dir.exists():
        return None
    # Prefer Qwen, then any other llamafile
    for pattern in ['*Qwen*', '*qwen*', '*.llamafile']:
        for path in llm_dir.glob(pattern):
            if path.is_file() and path.suffix == '.llamafile':
                return path
    return None


def find_zim_files():
    zim_dir = DIRS['kiwix_data']
    if not zim_dir.exists():
        return []
    return list(zim_dir.glob('*.zim'))


def start_kiwix():
    if check_port(KIWIX_PORT):
        print(f"  Kiwix already running on port {KIWIX_PORT}")
        return True
    
    kiwix_serve = find_kiwix_serve()
    zim_files = find_zim_files()
    
    if not kiwix_serve:
        print("  Kiwix server not found")
        return False
    
    if not zim_files:
        print("  No ZIM files found")
        return False
    
    print(f"  Starting Kiwix with {len(zim_files)} ZIM file(s)...")
    
    cmd = [str(kiwix_serve), '--port', str(KIWIX_PORT)]
    cmd.extend(str(z) for z in zim_files)
    
    try:
        if sys.platform != 'win32':
            os.chmod(kiwix_serve, 0o755)
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        processes.append(process)
        
        for _ in range(10):
            time.sleep(0.5)
            if check_port(KIWIX_PORT):
                print(f"  Kiwix started on port {KIWIX_PORT}")
                return True
        
        print("  Kiwix may not have started correctly")
        return False
    except Exception as e:
        print(f"  Failed to start Kiwix: {e}")
        return False


def start_llamafile():
    if check_port(LLAMAFILE_PORT):
        print(f"  AI already running on port {LLAMAFILE_PORT}")
        return True
    
    llamafile = find_llamafile()
    if not llamafile:
        print("  Llamafile not found (AI will be unavailable)")
        return False
    
    print(f"  Starting AI ({llamafile.name})...")
    
    try:
        if sys.platform != 'win32':
            os.chmod(llamafile, 0o755)
        
        # On macOS, llamafiles need to be run via sh
        # Use --server --nobrowser for headless API mode
        if sys.platform == 'darwin':
            cmd = ['sh', str(llamafile), '--server', '--nobrowser', '--port', str(LLAMAFILE_PORT), '--host', '127.0.0.1']
        else:
            cmd = [str(llamafile), '--server', '--nobrowser', '--port', str(LLAMAFILE_PORT), '--host', '127.0.0.1']
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        processes.append(process)
        
        print("  Waiting for AI to load", end='', flush=True)
        for _ in range(60):
            time.sleep(1)
            print('.', end='', flush=True)
            if check_port(LLAMAFILE_PORT):
                print()
                print(f"  AI started on port {LLAMAFILE_PORT}")
                return True
        
        print()
        print("  AI may still be loading")
        return False
    except Exception as e:
        print(f"  Failed to start AI: {e}")
        return False


def cleanup():
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


# =============================================================================
# MAIN
# =============================================================================

def main():
    print()
    print("  Knowledge Archive")
    print("  " + "=" * 40)
    print()
    print(f"  Location: {ARCHIVE_ROOT}")
    print()
    
    signal.signal(signal.SIGINT, lambda s, f: (cleanup(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (cleanup(), sys.exit(0)))
    
    print("  Starting services...")
    build_word_index()
    load_music_text_index()
    start_kiwix()
    detect_gutenberg_zim()
    load_gutenberg_catalog()

    ai_thread = threading.Thread(target=start_llamafile, daemon=True)
    ai_thread.start()
    
    print()
    print(f"  Starting server on port {PORT}...")
    
    handler = partial(ArchiveHandler, archive_root=ARCHIVE_ROOT)
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}"
        print()
        print("  " + "=" * 40)
        print(f"  Ready: {url}")
        print("  " + "=" * 40)
        print()
        print("  Press Ctrl+C to stop")
        print()
        
        try:
            webbrowser.open(url)
        except Exception:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Shutting down...")
        finally:
            cleanup()


if __name__ == "__main__":
    main()