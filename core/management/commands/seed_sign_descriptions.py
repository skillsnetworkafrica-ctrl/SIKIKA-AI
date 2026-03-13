from django.core.management.base import BaseCommand
from core.models import GlossaryTerm

# ASL sign descriptions for glossary terms
# These describe how to physically perform the sign in American Sign Language
SIGN_DATA = {
    'algorithm': 'Fingerspell A-L-G-O. In classroom ASL, often signed as STEP + STEP + PROCESS (both hands moving in alternating forward circles).',
    'data structure': 'Sign DATA (D-hands tap alternating on palm) + STRUCTURE (stack flat hands building upward).',
    'recursion': 'Sign AGAIN + SELF — point back at yourself with index finger, then circle hand repeating the motion, getting smaller each time.',
    'variable': 'V-hand rocks side to side (showing something that can change). Like the sign for CHANGE but with V-handshape.',
    'function': 'F-hand circles forward on open palm (a process that works on something). Similar to MACHINE but with F-hand.',
    'loop': 'Index finger draws a circle in the air repeatedly — the circular motion represents repeating code.',
    'array': 'Both flat hands side by side, slide apart horizontally — showing a row of items lined up.',
    'class': 'Both C-hands circle forward from body, palms facing each other — a group of related things.',
    'object': 'O-hand taps open palm twice — a concrete thing you can work with.',
    'inheritance': 'One hand above the other, top hand drops attributes down to lower hand — passing down properties.',
    'abstraction': 'Flat hand covers fist (hiding the details), then lifts slightly to show just the top.',
    'encapsulation': 'Both cupped hands wrap around each other — bundling things together inside a container.',
    'polymorphism': 'One hand shape-shifts between different handshapes (fist, flat, point) — taking many forms.',
    'stack': 'Flat hands stack one on top of the other, building upward — last in, first out.',
    'queue': 'Both flat hands in a line, back hand moves to front — first in, first out.',
    'compiler': 'C-hand sweeps over flat palm transforming into a different handshape — translating code.',
    'interpreter': 'Both F-hands rotate alternating at wrists — translating between two sides.',
    'api': 'Fingerspell A-P-I. Can also sign CONNECT (link both index fingers) + RULES (R-hand taps down palm).',
    'debugging': 'Pinch and pull bugs off flat palm (other hand) — literally removing bugs from code.',
    'database': 'D-hand stacks on top of flat palm repeatedly — layers of stored data. Or fingerspell D-B.',
    'network': 'Both 5-hands, fingertips touch, pull apart and reconnect at different points — nodes connecting.',
    'hypothesis': 'H-hand at forehead (THINK) then pushes forward with questioning expression — a proposed idea to test.',
    'theory': 'T-hand at forehead circles forward — an idea or framework of understanding.',
    'experiment': 'Both E-hands alternately pour downward — like pouring chemicals in beakers, testing ideas.',
    'analysis': 'Both bent V-hands pull apart (breaking something into pieces to examine).',
    'research': 'R-hand sweeps across open flat palm — searching through material.',
    'variable': 'V-hand rocks side to side — something that changes or varies.',
    'equation': 'Both flat hands face each other, bob up and down alternately to balance — showing equality.',
    'probability': 'P-hand wobbles side to side — uncertain, could go either way. Add NUMBER sign for context.',
    'theorem': 'T-hand at forehead then stamps onto palm — a proven truth or principle.',
    'derivative': 'D-hand slides along the other forearm with changing speed — rate of change along a curve.',
    'integral': 'Open hand sweeps under curved other hand — summing up the area under a curve.',
    'photosynthesis': 'Sign LIGHT (flick open hand near face) + PLANT (hand grows up through other hand) + MAKE.',
    'mitosis': 'Closed fist splits into two fists moving apart — one cell becoming two.',
    'osmosis': 'Wiggle fingers of one hand passing through flat other hand — particles moving through a membrane.',
    'genome': 'G-hand traces a double helix spiral downward — the twisted ladder of DNA.',
    'protein': 'P-hand links with other P-hand in a chain — amino acids linking together.',
    'supply': 'Flat hand pushes items forward from body — providing or offering goods.',
    'demand': 'Grabbing motion pulling toward body — wanting or requiring something.',
    'inflation': 'Both flat palms facing down rise upward together — prices going up.',
    'gdp': 'Fingerspell G-D-P. Can also sign COUNTRY + TOTAL + MAKE (total production of a nation).',
    'sustainability': 'Sign CONTINUE (both A-hands push forward) + GREEN (S-hand shakes at shoulder) — keeping things going in balance.',
}


class Command(BaseCommand):
    help = 'Seed ASL sign descriptions for existing glossary terms'

    def handle(self, *args, **options):
        updated = 0
        for term_lower, desc in SIGN_DATA.items():
            count = GlossaryTerm.objects.filter(
                term__iexact=term_lower,
                sign_description='',
            ).update(sign_description=desc)
            updated += count

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} glossary terms with sign descriptions.'))
