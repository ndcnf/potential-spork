import { FESTIVAL_DAY_CUTOFF_HOUR, screeningsOverlapWithBuffer } from '@/lib/planning'
import type { Cycle, Film, Priority, Screening } from '@/types'

type PreviewCycle = {
  slug: string
  name: string
  color: string | null
}

type PreviewFilm = {
  slug: string
  title: string
  cycle: string | null
  director: string | null
  tagline: string | null
  details: string | null
  status?: string
}

type PreviewScreening = {
  film_slug: string
  date: string
  venue_slug: string
  start_time: string
  ticket_url?: string | null
}

const cyclesSource: PreviewCycle[] = [
  { slug: 'international-competition', name: 'International competition', color: '#ff3b30' },
  { slug: 'third-kind', name: 'Third Kind', color: '#ffd60a' },
  { slug: 'ultra-movies', name: 'Ultra Movies', color: '#d7df01' },
  { slug: 'take-care', name: 'Take Care', color: '#007c73' },
  { slug: 'nifff-invasion', name: 'NIFFF Invasion', color: '#352c7a' },
]

const venues = {
  'passage-1': 'Passage 1',
  arcades: 'Arcades',
  rex: 'Rex',
  studio: 'Studio',
  'open-air': 'Open Air',
} as const

const filmSource: PreviewFilm[] = [
  { slug: 'alpha', title: 'Alpha', cycle: 'international-competition', director: 'Julia Ducournau', tagline: 'Marble-skin Allegory', details: "FR/BE, 2025, 128'" },
  { slug: 'a-cure-for-wellness', title: 'A Cure for Wellness', cycle: 'take-care', director: 'Gore Verbinski', tagline: 'Eurotrash Wellness Horror', details: "DE/LU/US, 2016, 146'" },
  { slug: 'dangerous-animals', title: 'Dangerous Animals', cycle: 'ultra-movies', director: 'Sean Byrne', tagline: 'Sharkcore', details: "AU/US/CA, 2025, 92'" },
  { slug: 'clown-in-a-cornfield', title: 'Clown in a Cornfield', cycle: 'ultra-movies', director: 'Eli Craig', tagline: 'Bozo goes Beserk', details: "US, 2025, 97'" },
  { slug: 'cloud', title: 'Cloud', cycle: 'third-kind', director: 'Kiyoshi Kurosawa', tagline: 'Dead End Digital Noir', details: "JP, 2024, 124'" },
  { slug: 'eddington', title: 'Eddington', cycle: 'third-kind', director: 'Ari Aster', tagline: 'Madness Always Grips America', details: "US/FI, 2025, 148'" },
  { slug: 'dead-talents-society', title: 'Dead Talents Society', cycle: 'ultra-movies', director: 'John Hsu', tagline: 'Feel Good Ghost Story', details: "TW, 2024, 111'" },
  { slug: 'dogtooth', title: 'Dogtooth', cycle: 'take-care', director: 'Yorgos Lanthimos', tagline: 'Kin Control Fable', details: "GR, 2009, 97'" },
  { slug: 'fantastic-shorts', title: 'Fantastic Shorts', cycle: 'nifff-invasion', director: null, tagline: null, details: "CH, 2025, 60'" },
  { slug: 'gatillero', title: 'Gatillero', cycle: 'third-kind', director: 'Cristian Tapia Marchiori', tagline: 'Revolt never truly dies', details: "AR, 2025, 80'" },
  { slug: 'hallow-road', title: 'Hallow Road', cycle: 'third-kind', director: 'Babak Anvari', tagline: 'Hit and run anxiety', details: "UK/IE/FI/US, 2025, 80'" },
  { slug: 'jimmy-and-stiggs', title: 'Jimmy and Stiggs', cycle: 'ultra-movies', director: 'Joe Begos', tagline: 'DIY Splatter Satire', details: "US, 2024, 80'" },
  { slug: 'monkey-shines', title: 'Monkey Shines', cycle: 'take-care', director: 'George A. Romero', tagline: 'Primate Psycho Thriller', details: "US, 1988, 113'" },
  { slug: 'the-home', title: 'The Home', cycle: 'international-competition', director: 'Mattias J. Skoglund', tagline: 'Old Age. New Fear', details: "SE/IS/EE, 2025, 87'" },
  { slug: 'the-rule-of-jenny-pen', title: 'The Rule of Jenny Pen', cycle: 'third-kind', director: 'James Ashcroft', tagline: 'Geriatric Terror', details: "NZ, 2024, 104'" },
  { slug: 'the-ugly-stepsister', title: 'The Ugly Stepsister', cycle: 'international-competition', director: 'Emilie Blichfeldt', tagline: 'Cinderella B Side goes Ballistic', details: "NO/SE/PL/DK/RO, 2025, 105'" },
  { slug: 'together', title: 'Together', cycle: null, director: null, tagline: null, details: null, status: 'not_found_in_wayback_capture' },
]

const screeningSource: PreviewScreening[] = [
  { film_slug: 'alpha', date: '2025-07-05', venue_slug: 'passage-1', start_time: '22:15' },
  { film_slug: 'alpha', date: '2025-07-09', venue_slug: 'passage-1', start_time: '19:15' },
  { film_slug: 'alpha', date: '2025-07-11', venue_slug: 'studio', start_time: '14:00' },
  { film_slug: 'a-cure-for-wellness', date: '2025-07-04', venue_slug: 'studio', start_time: '14:00' },
  { film_slug: 'dangerous-animals', date: '2025-07-05', venue_slug: 'studio', start_time: '22:15' },
  { film_slug: 'dangerous-animals', date: '2025-07-10', venue_slug: 'arcades', start_time: '22:00' },
  { film_slug: 'clown-in-a-cornfield', date: '2025-07-04', venue_slug: 'open-air', start_time: '00:45' },
  { film_slug: 'clown-in-a-cornfield', date: '2025-07-11', venue_slug: 'arcades', start_time: '00:30' },
  { film_slug: 'cloud', date: '2025-07-08', venue_slug: 'passage-1', start_time: '14:00' },
  { film_slug: 'cloud', date: '2025-07-11', venue_slug: 'passage-1', start_time: '11:00' },
  { film_slug: 'eddington', date: '2025-07-06', venue_slug: 'passage-1', start_time: '13:30' },
  { film_slug: 'eddington', date: '2025-07-11', venue_slug: 'passage-1', start_time: '19:45' },
  { film_slug: 'dead-talents-society', date: '2025-07-07', venue_slug: 'open-air', start_time: '21:45' },
  { film_slug: 'dead-talents-society', date: '2025-07-11', venue_slug: 'rex', start_time: '19:30' },
  { film_slug: 'dogtooth', date: '2025-07-11', venue_slug: 'rex', start_time: '11:00' },
  { film_slug: 'fantastic-shorts', date: '2025-07-07', venue_slug: 'rex', start_time: '11:00' },
  { film_slug: 'gatillero', date: '2025-07-05', venue_slug: 'arcades', start_time: '00:30' },
  { film_slug: 'gatillero', date: '2025-07-11', venue_slug: 'arcades', start_time: '14:15' },
  { film_slug: 'hallow-road', date: '2025-07-08', venue_slug: 'open-air', start_time: '00:15' },
  { film_slug: 'hallow-road', date: '2025-07-12', venue_slug: 'arcades', start_time: '17:00' },
  { film_slug: 'jimmy-and-stiggs', date: '2025-07-06', venue_slug: 'open-air', start_time: '00:15' },
  { film_slug: 'jimmy-and-stiggs', date: '2025-07-09', venue_slug: 'arcades', start_time: '00:30' },
  { film_slug: 'monkey-shines', date: '2025-07-12', venue_slug: 'arcades', start_time: '00:45' },
  { film_slug: 'the-home', date: '2025-07-06', venue_slug: 'arcades', start_time: '14:00' },
  { film_slug: 'the-home', date: '2025-07-08', venue_slug: 'arcades', start_time: '22:00' },
  { film_slug: 'the-home', date: '2025-07-11', venue_slug: 'studio', start_time: '17:00' },
  { film_slug: 'the-rule-of-jenny-pen', date: '2025-07-06', venue_slug: 'open-air', start_time: '21:45' },
  { film_slug: 'the-rule-of-jenny-pen', date: '2025-07-09', venue_slug: 'studio', start_time: '17:00' },
  { film_slug: 'the-ugly-stepsister', date: '2025-07-04', venue_slug: 'studio', start_time: '22:00' },
  { film_slug: 'the-ugly-stepsister', date: '2025-07-07', venue_slug: 'passage-1', start_time: '19:45' },
  { film_slug: 'the-ugly-stepsister', date: '2025-07-10', venue_slug: 'passage-1', start_time: '22:15' },
]

const cyclePriorities: Record<string, Priority> = {
  'international-competition': 'unreviewed',
  'third-kind': 'unreviewed',
  'ultra-movies': 'unreviewed',
  'take-care': 'unreviewed',
  'nifff-invasion': 'unreviewed',
}

const filmPriorities: Record<string, Priority> = {
  alpha: 'unreviewed',
  'the-ugly-stepsister': 'unreviewed',
  eddington: 'unreviewed',
  cloud: 'unreviewed',
  'dangerous-animals': 'unreviewed',
  'the-home': 'unreviewed',
  'the-rule-of-jenny-pen': 'unreviewed',
  'dead-talents-society': 'unreviewed',
  'a-cure-for-wellness': 'unreviewed',
  'clown-in-a-cornfield': 'unreviewed',
  dogtooth: 'unreviewed',
  gatillero: 'unreviewed',
  'hallow-road': 'unreviewed',
  'jimmy-and-stiggs': 'unreviewed',
  'monkey-shines': 'unreviewed',
  'fantastic-shorts': 'unreviewed',
  together: 'unreviewed',
}

const selectedScreenings = new Map<string, 'tentative' | 'confirmed'>()

const filmDetails: Record<string, { language: string | null; age: string | null; synopsis: string | null; posterUrl: string | null }> = {
  alpha: {
    language: 'français ov sub en',
    age: '16',
    synopsis:
      'France, années 80. Alpha, 13 ans, rentre d’une fête avec un tatouage maison. Sa mère flippe : un virus étrange circule, transformant ses victimes en statues de marbre. Pendant que la tension monte, l’oncle Amin, toxicomane et malade, débarque à la maison. Un récit fiévreux sur l’adolescence, la peur, les mutations silencieuses.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1117436/accessories/1781729.jpeg',
  },
  'a-cure-for-wellness': {
    language: 'English, German ov sub en',
    age: '16',
    synopsis: null,
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1084397/accessories/1784372.jpeg',
  },
  'dangerous-animals': {
    language: 'anglais ov sub fr',
    age: '16',
    synopsis:
      "Une surfeuse est enlevée par un tueur aux méthodes peu orthodoxes : il enferme ses victimes sur son chalutier pour les donner en pâture aux squales affamés de la côte australienne sous l'œil de sa caméra. Débute alors pour la jeune femme une lutte pour survivre… Une relecture du sous-genre horrifique du film de requins qui fait le choix audacieux de le croiser avec la figure du tueur en série et met en scène une héroïne dure à cuire dans la pure tradition du slasher.",
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1099498/accessories/1783912.jpeg',
  },
  'clown-in-a-cornfield': {
    language: 'English ov',
    age: '16',
    synopsis:
      'Quinn vient d’emménager à Kettle Springs, où elle découvre une communauté troublée par le récent incendie d’une usine locale. Mais au cœur des tensions, un danger plus inquiétant encore surgit d’un champ de maïs : le clown Frendo. Dans la plus pure tradition du slasher 80’s, CLOWN IN A CORNFIELD se réapproprie le motif du clown tueur dans un jeu de massacre sanglant, reflet d’une Amérique toujours plus recroquevillée sur ses propres peurs.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1090561/accessories/1783906.jpeg',
  },
  cloud: {
    language: 'japonais ov sub fr/en',
    age: '16',
    synopsis:
      'Coincé dans un travail qu’il abhorre, Yoshii comble ses fins de mois en faisant de la vente en ligne, devenant de plus en plus appâté par le gain. Son avarice va pourtant le rattraper, quand il se trouve pris dans une toile avec des ennemis bien réels. Une plongée des plus sombres de l’autre côté du miroir noir. Déjà à l’honneur du NIFFF en 2005, et après plusieurs sélections, le grand cinéaste japonais revient avec un objet cinématographique aussi intrigant que glaçant.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1057067/accessories/1783364.jpeg',
  },
  eddington: {
    language: 'anglais ov sub fr',
    age: '16',
    synopsis:
      'Mai 2020, Nouveau-Mexique. En pleine pandémie, un shérif conspirationniste affronte un maire progressiste sur fond de masques, fake news, tension raciale et violence latente. À travers cette fable grinçante, Ari Aster dresse le portrait d’une Amérique fracturée, en crise d’identité, de confiance et de vérité. EDDINGTON détourne les codes du western et du thriller politique pour en faire un huis clos à ciel ouvert, abrasif et visionnaire, sur l’implosion sanglante d’un pays.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1117435/accessories/1785515.jpeg',
  },
  'dead-talents-society': {
    language: 'min nan chinese, mandarin ov sub en',
    age: '16',
    synopsis:
      'Dans cette comédie horrifique, une femme fraîchement débarquée dans le monde des morts découvre le dur fonctionnement de ce dernier : les fantômes doivent exceller dans l’exercice de terroriser les vivants, sous peine d’être définitivement oubliés. Sur les conseils de Makoto, un agent pour spectres, elle s’associe à Catherine, une star de l’au-delà sur le déclin, pour donner un nouveau souffle à l’ambiance de l’hôtel qu’elles sont supposées hanter.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1058904/accessories/1783913.jpeg',
  },
  dogtooth: {
    language: 'grec ov sub fr',
    age: '16',
    synopsis:
      'Une maison bordée d’une haute clôture. Coupée du monde extérieur, la vie de trois adolescent·es est rythmée par le modèle imposé par leurs parents : protection ou maltraitance ?',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1084420/accessories/1784379.jpeg',
  },
  gatillero: {
    language: 'espagnol ov sub fr/en',
    age: '16',
    synopsis:
      'Libéré, un ancien taulard rêve de revoir sa fille. Mais le job de trop vire à la course-poursuite façon JOHN WICK sous tequila. Piégé dans un barrio en flammes, il enchaîne bastons, trahisons et règlements de comptes. GATILLERO, c’est le western urbain que Tarantino aurait tourné avec une GoPro et un shot de mezcal.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1089314/accessories/1783876.jpeg',
  },
  'hallow-road': {
    language: 'anglais ov sub fr',
    age: '16',
    synopsis:
      'Un coup de fil en pleine nuit : leur fille a fauché une inconnue sur une route paumée au milieu des bois. Les parents débarquent pour gérer le chaos… mais ce qui devait être un plan de crise vire au cauchemar. Entre forêt hantée, décisions foireuses et secrets familiaux, HALLOW ROAD embarque dans un thriller nocturne tendu, où rien ne se passe comme prévu.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1107246/accessories/1786069.jpeg',
  },
  'jimmy-and-stiggs': {
    language: 'anglais ov',
    age: '16',
    synopsis:
      'Jimmy, un cinéaste alcoolique et toxicomane au chômage, se terre dans son appartement de Los Angeles et sombre peu à peu dans une incontrôlable crise de nerfs. Convaincu d’avoir été enlevé par des extraterrestres et craignant leur retour, il demande à son vieil ami Stiggs de lui prêter main forte dans les préparatifs d’une guerre à venir. Une jouissive comédie horrifique dans la lignée des EVIL DEAD de Sam Raimi ou du BAD TASTE de Peter Jackson.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1062992/accessories/1783916.jpeg',
  },
  'monkey-shines': {
    language: 'anglais ov sub fr',
    age: '16',
    synopsis: null,
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1129853/accessories/1784385.jpeg',
  },
  'the-home': {
    language: 'suédois ov sub fr/en',
    age: '16',
    synopsis:
      'Des années après avoir quitté sa ville natale, Joel revient au bercail pour s’occuper de sa mère. Celle-ci a récemment frôlé la mort et doit emménager dans une résidence pour personnes âgées. Logeant dans la maison de son enfance le temps d’y faire du tri, le jeune homme va devoir affronter de sombres souvenirs, dont celui de son père violent… Entre drame familial et film de fantômes, un récit fantastique aussi terrifiant que déchirant.',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1091270/accessories/1781737.jpeg',
  },
  'the-rule-of-jenny-pen': {
    language: 'English ov sub fr',
    age: '16',
    synopsis:
      'Bientôt à la retraite, le juge Stefan Mortensen est victime d’un AVC en plein tribunal. Diminué, il emménage temporairement dans une maison de repos. Il y fait la connaissance de Dave Crealy, un résident qui prend un malin plaisir à persécuter ses congénères à l’aide d’une poupée nommée Jenny Pen... Face à un Geoffrey Rush impeccable, John Lithgow s’en donne à cœur joie en vieux psychopathe, dans un thriller horrifique des plus glaçants !',
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1062957/accessories/1783904.jpeg',
  },
  'the-ugly-stepsister': {
    language: 'norvégien ov sub fr/en',
    age: '16',
    synopsis:
      "Dans un royaume régi par la beauté, Elvira a recours aux méthodes les plus extrêmes pour remporter le cœur du prince. Dans ce premier long-métrage inspiré de CENDRILLON, la réalisatrice norvégienne Emilie Blichfeldt livre par le prisme du body horror une réflexion sur la féminité dans laquelle l'automutilation devient un moyen de prendre soin de soi et de son image. Fun et grotesque.",
    posterUrl: 'https://files.eventival.com/357/editions/2589/films/1082635/accessories/1781740.jpeg',
  },
}

const filmHeaderDetails: Record<string, { premiereLabel: string | null; shortDescription: string | null }> = {
  alpha: {
    premiereLabel: 'International Premiere',
    shortDescription:
      'Années 80. Alpha, 13 ans, rentre d’une fête avec un tatouage maison. Sa mère panique : un virus mystérieux rôde. Un trouble s’installe entre parano, mutation et fièvre adolescente.',
  },
  'a-cure-for-wellness': {
    premiereLabel: null,
    shortDescription:
      'Dans un centre de bien-être isolé dans les Alpes, un jeune cadre croit venir chercher la santé… mais trouve le délire. Une plongée hypnotique entre thriller clinique et fièvre gothique.',
  },
  'dangerous-animals': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'Une surfeuse est enlevée par un tueur en série sanguinaire qui donne ses victimes en pâture à des requins depuis son chalutier. Débute alors pour la jeune femme une lutte pour survivre.',
  },
  'clown-in-a-cornfield': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'À Kettle Springs, petite ville plongée dans une atmosphère pesante à la suite d’un incendie suspect, un clown tueur commence à sévir… Du slasher old school sur fond d’Amérique rurale.',
  },
  cloud: {
    premiereLabel: 'Romandie Premiere',
    shortDescription:
      'Un ouvrier plaque tout pour devenir revendeur en ligne, se retrouvant plongé dans un monde qu’il ne contrôle pas. Le danger n’est plus derrière l’écran, il est partout.',
  },
  eddington: {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'Nouveau-Mexique, 2020. Masques, tensions raciales, complotisme et virus. EDDINGTON ausculte l’Amérique en crise, entre western crépusculaire et satire toxique de la peur contemporaine.',
  },
  'dead-talents-society': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'Grâce à un agent pour fantômes, une femme fraîchement débarquée dans le monde des morts s’associe à une star de l’au-delà sur le déclin pour exceller dans l’art de terrifier les vivants.',
  },
  dogtooth: {
    premiereLabel: null,
    shortDescription: null,
  },
  gatillero: {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'Sorti de taule, "El Galgo" veut juste revoir sa gamine. Mais un plan à la BREAKING BAD tourne NARCOS version cauchemar : trahi, accusé, traqué… et armé jusqu’aux dents.',
  },
  'hallow-road': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      '2h du matin. Leur fille a renversé quelqu’un sur une route paumée. Ils foncent pour la couvrir, mais tout dérape. Une virée nocturne tendue entre secrets, peur et mauvais karma.',
  },
  'jimmy-and-stiggs': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'Dans cette comédie horrifique aux accents fluo, un cinéaste au chômage convaincu d’avoir été enlevé par des extraterrestres appelle un vieil ami à la rescousse pour préparer la guerre depuis son appartement.',
  },
  'monkey-shines': {
    premiereLabel: null,
    shortDescription:
      'Paralysé après un accident, un homme reçoit l’aide d’un singe dressé… qui développe un lien télépathique et une soif meurtrière. Un thriller cruel où la dépendance vire au cauchemar.',
  },
  'the-home': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'De retour dans sa ville natale pour accompagner l’emménagement de sa mère dans une maison de retraite, Joel va devoir affronter de sombres souvenirs, dont celui de son père violent.',
  },
  'the-rule-of-jenny-pen': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      "À la suite d'un AVC, un vieux juge emménage dans une maison de repos, où un résident psychopathe prend un malin plaisir à persécuter ses congénères à l’aide d’une étrange poupée.",
  },
  'the-ugly-stepsister': {
    premiereLabel: 'Swiss Premiere',
    shortDescription:
      'Dans cette relecture de Cendrillon à la sauce body horror, la demi-soeur jalouse recourt aux extrêmes pour gagner la course à la perfection et le coeur du prince. Haut-le-coeur garantis.',
  },
}

const filmCast: Record<string, string | null> = {
  alpha: 'Tahar Rahim, Golshifteh Farahani, Mélissa Boros',
  'a-cure-for-wellness': 'Dane DeHaan, Jason Isaacs, Mia Goth',
  'dangerous-animals': 'Hassie Harrison, Josh Heuston, Jai Courtney',
  'clown-in-a-cornfield': 'Katie Douglas, Aaron Abrams, Carson MacCormac',
  cloud: 'Masaki Suda, Kotone Furukawa, Daiken Okudaira',
  eddington: 'Joaquin Phoenix, Pedro Pascal, Emma Stone, Austin Butler',
  'dead-talents-society': 'Gingle Wang, Sandrine Pinna, Chen Bolin',
  dogtooth: 'Christos Stergioglou, Michele Valley, Angeliki Papoulia',
  gatillero: 'Sergio Podelei, Julieta Díaz, Ramiro Blas',
  'hallow-road': 'Rosamund Pike, Matthew Rhys',
  'jimmy-and-stiggs': 'Joe Begos, Matt Mercer, Riley Dandy',
  'monkey-shines': 'Jason Beghe, John Pankow, Kate McNeil',
  'the-home': 'Philip Oros, Gizem Erdogan, Anki Lidén, Bengt Cw Carlsson',
  'the-rule-of-jenny-pen': 'John Lithgow, Geoffrey Rush, Nikki MacDonnell, Maaka Pohatu',
  'the-ugly-stepsister': 'Lea Myren, Thea Sofie Loch Naess, Ane Dahl Torp',
}

function parseDetails(details: string | null): { countries: string | null; year: number | null; duration: number | null } {
  if (!details) {
    return { countries: null, year: null, duration: null }
  }

  const match = details.match(/^(.*?),\s*(\d{4}),\s*(\d+)'$/)
  if (!match) {
    return { countries: details, year: null, duration: null }
  }

  return {
    countries: match[1],
    year: Number(match[2]),
    duration: Number(match[3]),
  }
}

function computeEnd(start: string, duration: number | null): string {
  const date = new Date(start)
  date.setMinutes(date.getMinutes() + (duration ?? 120))
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}

function buildRealStart(dateLabel: string, startTime: string): string {
  const [year, month, day] = dateLabel.split('-').map(Number)
  const [hours, minutes] = startTime.split(':').map(Number)
  const realDate = new Date(year, month - 1, day, hours, minutes, 0)

  if (hours < FESTIVAL_DAY_CUTOFF_HOUR) {
    realDate.setDate(realDate.getDate() + 1)
  }

  const realYear = realDate.getFullYear()
  const realMonth = String(realDate.getMonth() + 1).padStart(2, '0')
  const realDay = String(realDate.getDate()).padStart(2, '0')
  const realHours = String(realDate.getHours()).padStart(2, '0')
  const realMinutes = String(realDate.getMinutes()).padStart(2, '0')
  return `${realYear}-${realMonth}-${realDay}T${realHours}:${realMinutes}:00`
}

function buildFestivalFilmUrl(slug: string): string {
  return `https://nifff.ch/prog/2025/film/${slug}`
}

export function buildPreviewDataset(): { cycles: Cycle[]; films: Film[]; screenings: Screening[] } {
  const cycles: Cycle[] = cyclesSource.map((cycle, index) => ({
    id: index + 1,
    name: cycle.name,
    slug: cycle.slug,
    color: cycle.color,
    priority: cyclePriorities[cycle.slug] ?? 'unreviewed',
  }))

  const cycleBySlug = new Map(cycles.map((cycle) => [cycle.slug, cycle]))

  const films: Film[] = filmSource.map((film, index) => {
    const cycle = film.cycle ? cycleBySlug.get(film.cycle) ?? null : null
    const parsed = parseDetails(film.details)
    const detail = filmDetails[film.slug] ?? { language: null, age: null, synopsis: null, posterUrl: null }
    const headerDetail = filmHeaderDetails[film.slug] ?? { premiereLabel: null, shortDescription: null }

    return {
      id: index + 1,
      title: film.title,
      slug: film.slug,
      directors: film.director,
      year: parsed.year,
      countries: parsed.countries,
      duration_minutes: parsed.duration,
      tagline: film.tagline,
      premiere_label: headerDetail.premiereLabel,
      short_description: headerDetail.shortDescription,
      cast: film.status === 'not_found_in_wayback_capture' ? 'Absent de la capture Wayback croisee' : (filmCast[film.slug] ?? null),
      synopsis: detail.synopsis,
      language: detail.language,
      age_rating: detail.age,
      poster_url: detail.posterUrl,
      festival_url: film.status === 'not_found_in_wayback_capture' ? null : buildFestivalFilmUrl(film.slug),
      imdb_url: null,
      priority: filmPriorities[film.slug] ?? 'unreviewed',
      planning_type: 'standalone',
      cycle_id: cycle?.id ?? null,
      cycle_name: cycle?.name ?? null,
      cycle_color: cycle?.color ?? null,
    }
  })

  const filmBySlug = new Map(films.map((film) => [film.slug, film]))

  const screeningsBase: Screening[] = screeningSource.map((screening, index) => {
    const film = filmBySlug.get(screening.film_slug)
    const startsAt = buildRealStart(screening.date, screening.start_time)
    const status = selectedScreenings.get(`${screening.film_slug}|${screening.date}|${screening.start_time}`) ?? 'none'

    return {
      id: index + 1,
      film_id: film?.id ?? -1,
      film_title: film?.title ?? screening.film_slug,
      venue_id: index + 1,
      venue_name: venues[screening.venue_slug as keyof typeof venues] ?? screening.venue_slug,
      starts_at: startsAt,
      ends_at: computeEnd(startsAt, film?.duration_minutes ?? null),
      ticket_url: screening.ticket_url ?? null,
      selection_status: status,
      derived_state: 'available',
    }
  })

  const screenings = screeningsBase.map((screening) => {
    const selectedSibling = screeningsBase.find(
      (other) =>
        other.film_id === screening.film_id &&
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed'),
    )

    const conflictingSelected = screeningsBase.find(
      (other) =>
        other.id !== screening.id &&
        (other.selection_status === 'tentative' || other.selection_status === 'confirmed') &&
        screeningsOverlapWithBuffer(screening, other),
    )

    let derived: Screening['derived_state'] = 'available'
    if (screening.selection_status === 'tentative' || screening.selection_status === 'confirmed') {
      derived = 'selected'
    } else if (selectedSibling) {
      derived = 'disabled'
    } else if (conflictingSelected) {
      derived = 'conflict'
    }

    return { ...screening, derived_state: derived }
  })

  return { cycles, films, screenings }
}
