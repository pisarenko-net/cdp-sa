import re


class TOCError(Exception):
    pass


class Toc(object):
    # Confusingly, the CD format has it's own definition of frame.  There
    # are 75 CD frames per second, each consisting of 588 audio frames.
    PCM_FRAMES_PER_CD_FRAME = 588

    def __init__(self, toc):
        self.toc = toc
        self.disc_meta = self._parse_toc()

    def _parse_toc(self):
        disc_meta = {
            'tracks': []
        }

        track = None
        cd_text = CDText()

        iter_toc = self._iter_toc_lines()
        for line in iter_toc:
            if line in ('CD_DA', 'CD_ROM', 'CD_ROM_XA'):
                pass

            elif line.startswith('CATALOG '):
                pass

            # Start of a new track
            elif line.startswith('TRACK '):

                if track is not None:
                    disc_meta['tracks'].append(track)

                if line == 'TRACK AUDIO':
                    track = {}
                else:
                    # Just skip non-audio tracks
                    track = None

            # Ignore some track flags that don't matter to us
            elif line in ('TWO_CHANNEL_AUDIO',
                          'COPY', 'NO COPY',
                          'PRE_EMPHASIS', 'NO PRE_EMPHASIS'):
                pass

            # Anyone ever seen one of these discs?
            elif line == 'FOUR_CHANNEL_AUDIO':
                raise TOCError('no support for four-channel audio')

            # Implement CD_TEXT later
            elif line.startswith('CD_TEXT '):
                info = cd_text.parse(line[7:], iter_toc, track is None)
                if info:
                    if track is None:
                        disc_meta['artist'] = info.get('artist')
                        disc_meta['title'] = info.get('title')
                    else:
                        track['artist'] = info.get('artist')
                        track['title'] = info.get('title')

            # Pick up the offsets within the data file
            elif line.startswith('FILE '):
                p = line.split()

                # Just assume the last two are either 0 or an MSF
                if len(p) < 4:
                    raise TOCError('missing offsets in file: %s' % line)

                offset = p[-2]
                length = p[-1]

                if offset == '0':
                    track['file_offset'] = 0
                else:
                    try:
                        track['file_offset'] = self._msf_to_frames(offset)
                    except ValueError:
                        raise TOCError('bad offset for file: %s' % line)

                try:
                    track['file_length'] = self._msf_to_frames(length)
                except ValueError:
                    raise TOCError('bad length for file: %s' % line)

            elif line.startswith('SILENCE '):
                track['pregap_silence'] = self._get_toc_msf_arg(line)

            elif line.startswith('START '):
                track['pregap_offset'] = self._get_toc_msf_arg(line)

            elif line.startswith('INDEX '):
                pass

            elif line.startswith('ISRC '):
                pass

            elif line.startswith('DATAFILE '):
                pass

            elif line != '':
                raise TOCError('unexpected line: %s' % line)

        if track is not None:
            disc_meta['tracks'].append(track)

        # Make sure we did read an audio disc
        if not disc_meta['tracks']:
            raise TOCError('no audio tracks on disc')

        return disc_meta

    def _iter_toc_lines(self):
        for line in self.toc.split('\n'):
            # Strip comments and whitespace
            p = line.find('//')
            if p != -1:
                line = line[:p]

            line = line.strip()

            # Hand over non-empty lines
            if line:
                yield line

    def _get_toc_msf_arg(self, line):
        """Parse an MSF from a TOC line."""

        p = line.split()
        if len(p) != 2:
            raise TOCError(
                'expected a single MSF argument in line: %s' % line)

        try:
            return self._msf_to_frames(p[1])
        except ValueError:
            raise TOCError('bad MSF in line: %s' % line)

    def _msf_to_frames(self, msf):
        """Translate an MM:SS:FF to number of PCM audio frames."""

        d = msf.split(':')
        if len(d) != 3:
            raise ValueError(msf)

        m = int(d[0], 10)
        s = int(d[1], 10)
        f = int(d[2], 10)

        return (((m * 60) + s) * 75 + f) * Toc.PCM_FRAMES_PER_CD_FRAME


class CDText(object):
    LANGUAGE_MAP_RE = re.compile(r'LANGUAGE_MAP +\{')
    LANGUAGE_RE = re.compile(r'LANGUAGE +([0-9]+) +\{ *$')
    MAPPING_RE = re.compile(r'\b([0-9]+)\s*:\s*([0-9A-Z]+)\b')

    def __init__(self):
        self.language = None

    def parse(self, line, toc_iter, for_disc = False):
        """Parse a CD_TEXT block.
        Returns a dict with the extracted values, if any.
        """

        info = None

        if line.strip() != '{':
            raise TOCError('expected "{" but got "{0}"'.format(line))

        for line in toc_iter:
            if line == '}':
                return info

            m = self.LANGUAGE_MAP_RE.match(line)
            if m:
                if not for_disc:
                    raise TOCError('unexpected LANGUAGE_MAP in track CD_TEXT block')

                self.parse_language_map(line[m.end():], toc_iter)
                continue

            m = self.LANGUAGE_RE.match(line)
            if m:
                if self.language is None:
                    # No LANGUAGE_MAP, so just use whatever language
                    # ID we find here (it's probably 0)
                    self.language = m.group(1)

                if self.language == m.group(1):
                    info = self.parse_language_block(toc_iter)
                else:
                    # Just parse and throw away the result
                    self.parse_language_block(toc_iter)

                continue

            raise TOCError('unexpected CD_TEXT line: {0}'.format(line))

        raise TOCError('unexpected EOF in CD_TEXT block')

    def parse_language_map(self, line, toc_iter):
        i = line.find('}')
        if i != -1:
            # entire mapping on one line
            mapstr = line[:i]
        else:
            mapstr = line
            for line in toc_iter:
                i = line.find('}')
                if i != -1:
                    # end of mapping
                    mapstr += ' ' + line[:i]
                    break
                else:
                    mapstr += ' ' + line

        mappings = self.MAPPING_RE.findall(mapstr)
        for langnum, langcode in mappings:
            # Find an English code
            if langcode == '9' or langcode == 'EN':
                self.language = langnum
                return

        # Use first language mapping, if any
        if mappings:
            self.language = mappings[0][0]
        else:
            raise TOCError('found no language mappings: {0}'.format(mapstr))

    def parse_language_block(self, toc_iter):
        info = {}
        for line in toc_iter:
            if line == '}':
                return info
            elif line.startswith('TITLE '):
                info['title'] = self._get_toc_string_arg(line) or None
            elif line.startswith('PERFORMER '):
                info['artist'] = self._get_toc_string_arg(line) or None
            elif '{' in line:
                if '}' not in line:
                    self.skip_binary_data(toc_iter)

        raise TOCError('unexpected EOF in CD_TEXT LANGUAGE block')

    def skip_binary_data(self, toc_iter):
        for line in toc_iter:
            if '}' in line:
                return

        raise TOCError('unexpected EOF in binary CD_TEXT data')


    def _get_toc_string_arg(self, line):
        """Parse out a string argument from a TOC line."""
        s = line.find('"')
        if s == -1:
            raise TOCError('no string argument in line: %s' % line)

        e = line.find('"', s + 1)
        if s == -1:
            raise TOCError('no string argument in line: %s' % line)

        return line[s + 1 : e]
