import { useId, type ReactNode } from 'react'
import { Attr, Transfo } from './animation'
import { useMouvementReduit } from './useMouvementReduit'

// Tchouette : tchou-tchou + chouette. La face avant d'un petit train régional
// est le visage d'une chouette. Style « Memphis » : aplats, contours épais
// bleu nuit, ombre portée dure décalée. Animations en SMIL uniquement, jamais
// émises si l'utilisateur demande à réduire les animations.

export type HumeurTchouette = 'repos' | 'reflexion' | 'parle' | 'joie' | 'inquiete' | 'salue'

export interface TchouetteProps {
  /** Expression et animation de la mascotte. */
  humeur?: HumeurTchouette
  /** Largeur en pixels ; la hauteur suit le ratio du dessin (carré). */
  taille?: number
  /** Texte alternatif. Vide pour une mascotte purement décorative. */
  titre?: string
  className?: string
}

/* ---------- Palette de marque (fixe : un asset de marque ne suit pas le thème) ---------- */

const ROUGE = '#C8102E'
const ROUGE_FONCE = '#A00D24'
const NUIT = '#0B2341'
const NUIT_PROFONDE = '#071629'
const OR = '#FFCD00'
const BLANC = '#FFFFFF'
const BRUME = '#F4F5F7'

/* ---------- Géométrie (dessin centré sur x = 100) ---------- */

/** Cadre carré : marge pour le liseré, l'ombre décalée, les sauts et les ailes levées. */
const VIEWBOX = '-4 -10 214 214'
const CONTOUR = 6
const LISERE = CONTOUR + 8
const DECALAGE_OMBRE = 6
/** Symétrie gauche ↔ droite autour de l'axe x = 100. */
const MIROIR = 'matrix(-1 0 0 1 200 0)'

/** Cabine en dôme, presque un œuf ; le bas est caché par le châssis. */
const CORPS = 'M34 142 V102 C34 58 62 30 100 30 C138 30 166 58 166 102 V142 Q166 148 160 148 H40 Q34 148 34 142 Z'
/** Aigrette gauche en triangle, plume intérieure en zigzag façon pantographe (la droite est en miroir). */
const AIGRETTE = 'M56 62 L40 6 L94 38 Z'
const AIGRETTE_PLUME = 'M58 50 L47 19 L60 30 L64 22 L84 37 Z'
/** Volet latéral gauche (aile), avec deux lames d'aération comme des plumes. */
const AILE = 'M44 108 C30 110 21 122 21 141 Q21 148 28 148 H44 Z'
const AILE_LAMES = 'M29 127 H39 M27 137 H39'
const PIVOT_AILE = '44 110'
const ANGLE_AILE_LEVEE = 20
/** Coucou (`salue`) : l'aile gauche monte au-dessus de la tête puis s'agite. */
const ANGLE_SALUT = 122
const CYCLE_SALUT = 3.2
const PARE_BRISE = 'M76 40 H124 Q130 40 132.5 45 L137 54 Q139.5 59.5 133 59.5 H67 Q60.5 59.5 63 54 L67.5 45 Q70 40 76 40 Z'
const REFLET = 'M121 43.5 H127 L121.5 56 H115.5 Z'
const CHASSIS = { x: 40, y: 144, width: 120, height: 14, rx: 6 }
const ROUES = [70, 130] as const
const Y_ROUE = 166
const R_ROUE = 15
const YEUX = [70, 130] as const
const Y_YEUX = 102
const R_PHARE = 23
const R_BLANC = 15
const BEC = 'M88 118 H112 L100 136 Z'
const MACHOIRE = 'M94 127 L106 127 L100 137 Z'
const BOUCHE_FERMEE = 'M96 123 L104 123 L102 129 L100 131 L98 129 Z'
const BOUCHE_OUVERTE = 'M89 120 L111 120 L109 139 L100 146 L91 139 Z'
const SOURCIL = 'M52 81 L84 70'

interface Pose {
  /** Décalage des pupilles depuis le centre de l'œil. */
  regard: [number, number]
  rayonPupille: number
}

const POSES: Record<HumeurTchouette, Pose> = {
  repos: { regard: [0, 1.5], rayonPupille: 8.5 },
  reflexion: { regard: [-4.5, -5], rayonPupille: 8 },
  parle: { regard: [0, 0.5], rayonPupille: 8.5 },
  joie: { regard: [0, 0], rayonPupille: 8.5 },
  inquiete: { regard: [0, 1], rayonPupille: 5 },
  salue: { regard: [0, 0], rayonPupille: 8.5 },
}

/** Position des ailes : au repos, levées de joie, ou une seule levée pour saluer. */
type PoseAiles = 'repos' | 'levees' | 'salut'

function poseAiles(humeur: HumeurTchouette): PoseAiles {
  if (humeur === 'joie') return 'levees'
  if (humeur === 'salue') return 'salut'
  return 'repos'
}

/* ---------- Pièces ---------- */

/**
 * Paire d'ailes : la gauche telle quelle, la droite en miroir.
 * `levees` : les deux ailes battent ensemble. `salut` : seule l'aile gauche
 * monte, fait coucou deux ou trois fois, redescend, puis marque une pause.
 */
function Ailes({ pose, anime, children }: { pose: PoseAiles; anime: boolean; children: ReactNode }) {
  const haut = `${ANGLE_AILE_LEVEE} ${PIVOT_AILE}`
  const angle = (a: number) => `${a} ${PIVOT_AILE}`
  const gauche =
    pose === 'salut' ? (
      <g transform={`rotate(${angle(ANGLE_SALUT)})`}>
        {anime && (
          <Transfo
            type="rotate"
            valeurs={[angle(0), angle(ANGLE_SALUT), angle(100), angle(138), angle(100), angle(138), angle(108), angle(0), angle(0)]}
            temps={[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.75, 1]}
            duree={CYCLE_SALUT}
          />
        )}
        {children}
      </g>
    ) : (
      <g transform={pose === 'levees' ? `rotate(${haut})` : undefined}>
        {pose === 'levees' && anime && <Transfo type="rotate" valeurs={[haut, `-2 ${PIVOT_AILE}`, haut]} duree={0.45} />}
        {children}
      </g>
    )
  // L'aile droite bat avec la gauche en `levees`, reste baissée sinon.
  const droite = pose === 'levees' ? gauche : <g>{children}</g>
  return (
    <>
      {gauche}
      <g transform={MIROIR}>{droite}</g>
    </>
  )
}

/** Silhouette pleine d'une seule couleur : ombre portée et liseré d'autocollant. */
function Silhouette(props: { couleur: string; epaisseur: number; pose: PoseAiles; anime: boolean; roues: boolean }) {
  const { couleur, epaisseur, pose, anime, roues } = props
  return (
    <g fill={couleur} stroke={couleur} strokeWidth={epaisseur} strokeLinejoin="round">
      {[undefined, MIROIR].map((t) => (
        <g key={t ?? 'gauche'} transform={t}>
          <path d={AIGRETTE} />
        </g>
      ))}
      <Ailes pose={pose} anime={anime}>
        <path d={AILE} />
      </Ailes>
      <path d={CORPS} />
      {roues && (
        <>
          <rect {...CHASSIS} />
          {ROUES.map((x) => (
            <circle key={x} cx={x} cy={Y_ROUE} r={R_ROUE} />
          ))}
        </>
      )}
    </g>
  )
}

function Oeil({ cx, humeur, anime }: { cx: number; humeur: HumeurTchouette; anime: boolean }) {
  const { regard, rayonPupille } = POSES[humeur]
  const cligne = anime && (humeur === 'repos' || humeur === 'parle')
  return (
    <g transform={`translate(${cx} ${Y_YEUX})`}>
      <circle r={R_PHARE} fill={OR} stroke={NUIT} strokeWidth={5} />
      {humeur === 'joie' || humeur === 'salue' ? (
        <>
          <circle r={R_BLANC} fill={BLANC} stroke={NUIT} strokeWidth={2.5} />
          <path d="M-9 5 Q0 -12 9 5" fill="none" stroke={NUIT} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : (
        <>
          {/* Paupière, visible seulement pendant le clignement. */}
          <circle r={R_BLANC} fill={ROUGE_FONCE} />
          <g>
            {cligne && (
              <Transfo
                type="scale"
                valeurs={['1 1', '1 1', '1 0.08', '1 1']}
                temps={[0, 0.92, 0.96, 1]}
                duree={humeur === 'parle' ? 3.1 : 4.2}
                rythme="lineaire"
              />
            )}
            <circle r={R_BLANC} fill={BLANC} stroke={NUIT} strokeWidth={2.5} />
            <g transform={`translate(${regard[0]} ${regard[1]})`}>
              <circle r={rayonPupille} fill={NUIT} />
              <circle cx={-rayonPupille * 0.35} cy={-rayonPupille * 0.4} r={rayonPupille * 0.38} fill={BLANC} />
            </g>
          </g>
        </>
      )}
    </g>
  )
}

/** Bec-nez du train. En `parle`, la mandibule descend et dévoile la bouche. */
function Bec({ parle, anime }: { parle: boolean; anime: boolean }) {
  return (
    <g stroke={NUIT} strokeWidth={4} strokeLinejoin="round">
      {parle ? (
        <>
          <path d={BOUCHE_OUVERTE} fill={NUIT_PROFONDE}>
            {anime && <Attr nom="d" valeurs={[BOUCHE_OUVERTE, BOUCHE_FERMEE, BOUCHE_OUVERTE]} duree={0.34} />}
          </path>
          <path d={MACHOIRE} fill={OR} transform="translate(0 10)">
            {anime && <Transfo type="translate" valeurs={['0 10', '0 0', '0 10']} duree={0.34} />}
          </path>
        </>
      ) : (
        <path d={MACHOIRE} fill={OR} />
      )}
      <path d={BEC} fill={OR} />
    </g>
  )
}

/** Afficheur de destination : trois points or qui s'allument tour à tour quand elle réfléchit. */
function Afficheur({ reflechit, anime }: { reflechit: boolean; anime: boolean }) {
  return (
    <g>
      <rect x={82} y={43} width={36} height={12} rx={4} fill={NUIT_PROFONDE} />
      {[91, 100, 109].map((x, i) => (
        <circle key={x} cx={x} cy={49} r={3.2} fill={OR}>
          {reflechit && anime && (
            <Attr nom="opacity" valeurs={[0.2, 1, 0.2, 0.2]} temps={[0, 0.2, 0.45, 1]} duree={1.35} debut={i * 0.27} />
          )}
        </circle>
      ))}
    </g>
  )
}

function Roue({ cx, tourne }: { cx: number; tourne: boolean }) {
  return (
    <g transform={`translate(${cx} ${Y_ROUE})`}>
      <g>
        {tourne && <Transfo type="rotate" valeurs={[0, 360]} duree={0.9} rythme="lineaire" />}
        <circle r={R_ROUE} fill={OR} stroke={NUIT} strokeWidth={5} />
        <path d="M-9 0 H9 M0 -9 V9" stroke={NUIT} strokeWidth={3.5} strokeLinecap="round" />
        <circle r={5} fill={NUIT} />
      </g>
    </g>
  )
}

/** Étincelle or à quatre branches. */
function Etincelle({ x, y, rayon, debut, anime }: { x: number; y: number; rayon: number; debut: number; anime: boolean }) {
  const r = rayon
  const p = rayon * 0.28
  return (
    <g transform={`translate(${x} ${y})`}>
      <g>
        {anime && <Transfo type="scale" valeurs={[1, 0.5, 1]} duree={0.9} debut={debut} />}
        <path
          d={`M0 ${-r} L${p} ${-p} L${r} 0 L${p} ${p} L0 ${r} L${-p} ${p} L${-r} 0 L${-p} ${-p} Z`}
          fill={OR}
          stroke={NUIT}
          strokeWidth={3}
          strokeLinejoin="round"
        />
      </g>
    </g>
  )
}

/** Goutte de sueur de l'inquiétude. */
function Goutte({ anime }: { anime: boolean }) {
  return (
    <g transform="translate(174 58)">
      <g>
        {anime && (
          <>
            <Transfo type="translate" valeurs={['0 0', '0 0', '0 10']} temps={[0, 0.35, 1]} duree={1.8} rythme="lineaire" />
            <Attr nom="opacity" valeurs={[1, 1, 0]} temps={[0, 0.6, 1]} duree={1.8} rythme="lineaire" />
          </>
        )}
        <path
          d="M0 -10 C4 -4 7 0 7 4 A7 7 0 0 1 -7 4 C-7 0 -4 -4 0 -10 Z"
          fill={BRUME}
          stroke={NUIT}
          strokeWidth={3}
          strokeLinejoin="round"
        />
      </g>
    </g>
  )
}

/** Mouvement d'ensemble propre à chaque humeur. */
function MouvementGlobal({ humeur }: { humeur: HumeurTchouette }) {
  switch (humeur) {
    case 'repos':
      return <Transfo type="translate" valeurs={['0 0', '0 -3', '0 0']} duree={3.2} />
    case 'reflexion':
      return <Transfo type="translate" valeurs={['0 0', '0 -2', '0 0']} duree={4} />
    case 'parle':
      return <Transfo type="translate" valeurs={['0 0', '0 -1.5', '0 0']} duree={0.68} />
    case 'joie':
      return <Transfo type="translate" valeurs={['0 0', '0 -6', '0 0']} duree={0.9} />
    case 'salue':
      // Petit rebond calé sur les coucous de l'aile (3,2 s / 5 ≈ un rebond par coucou).
      return <Transfo type="translate" valeurs={['0 0', '0 -2.5', '0 0']} duree={CYCLE_SALUT / 5} />
    case 'inquiete':
      return (
        <Transfo
          type="translate"
          valeurs={['0 0', '-1.6 0', '1.6 0', '-1.2 0', '1.2 0', '0 0', '0 0']}
          temps={[0, 0.07, 0.14, 0.21, 0.28, 0.35, 1]}
          duree={1.5}
          rythme="lineaire"
        />
      )
  }
}

/* ---------- Composant ---------- */

export default function Tchouette({ humeur = 'repos', taille = 160, titre = 'Tchouette', className }: TchouetteProps) {
  const anime = !useMouvementReduit()
  // Identifiants SVG uniques par instance (plusieurs Tchouette par page).
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, '')
  const idTitre = `tchouette-titre-${id}`
  const idCorps = `tchouette-corps-${id}`
  const decoratif = !titre
  const joie = humeur === 'joie'
  const silhouette = { pose: poseAiles(humeur), anime }

  return (
    <svg
      // `key` : changer d'humeur remonte tout le SVG, ce qui remet son horloge SMIL à zéro.
      // Chaque animation repart donc de son début (le coucou commence aile baissée).
      key={humeur}
      xmlns="http://www.w3.org/2000/svg"
      viewBox={VIEWBOX}
      width={taille}
      height={taille}
      className={className}
      data-humeur={humeur}
      role={decoratif ? undefined : 'img'}
      aria-hidden={decoratif ? true : undefined}
      aria-labelledby={decoratif ? undefined : idTitre}
      focusable="false"
    >
      {!decoratif && <title id={idTitre}>{titre}</title>}
      <defs>
        <clipPath id={idCorps}>
          <path d={CORPS} />
        </clipPath>
      </defs>

      <g>
        {anime && <MouvementGlobal humeur={humeur} />}
        <g transform={humeur === 'reflexion' ? 'rotate(-5 100 170)' : undefined}>
          {/* Liseré blanc d'autocollant (lisible sur fond bleu nuit), puis ombre portée dure. */}
          <Silhouette couleur={BLANC} epaisseur={LISERE} roues {...silhouette} />
          <g transform={`translate(${DECALAGE_OMBRE} ${DECALAGE_OMBRE})`}>
            <Silhouette couleur={BLANC} epaisseur={LISERE} roues={false} {...silhouette} />
            <Silhouette couleur={NUIT} epaisseur={CONTOUR} roues={false} {...silhouette} />
          </g>

          {/* Aigrettes-pantographes */}
          {[undefined, MIROIR].map((t) => (
            <g key={t ?? 'gauche'} transform={t}>
              <path d={AIGRETTE} fill={ROUGE} stroke={NUIT} strokeWidth={CONTOUR} strokeLinejoin="round" />
              <path d={AIGRETTE_PLUME} fill={ROUGE_FONCE} />
            </g>
          ))}

          {/* Cabine : disque facial de chouette et bande de livrée, découpés au corps. */}
          <path d={CORPS} fill={ROUGE} />
          <g clipPath={`url(#${idCorps})`}>
            {YEUX.map((cx) => (
              <circle key={cx} cx={cx} cy={Y_YEUX} r={30} fill={ROUGE_FONCE} />
            ))}
            <rect x={0} y={137} width={200} height={8} fill={BRUME} />
          </g>
          <path d={CORPS} fill="none" stroke={NUIT} strokeWidth={CONTOUR} strokeLinejoin="round" />

          {/* Volets latéraux = ailes */}
          <Ailes pose={poseAiles(humeur)} anime={anime}>
            <path d={AILE} fill={ROUGE_FONCE} stroke={NUIT} strokeWidth={CONTOUR} strokeLinejoin="round" />
            <path d={AILE_LAMES} stroke={NUIT} strokeWidth={3.5} strokeLinecap="round" />
          </Ailes>

          {/* Pare-brise et afficheur de destination */}
          <path d={PARE_BRISE} fill={NUIT} stroke={NUIT} strokeWidth={3} strokeLinejoin="round" />
          <path d={REFLET} fill={BRUME} />
          <Afficheur reflechit={humeur === 'reflexion'} anime={anime} />

          {/* Yeux-phares */}
          {YEUX.map((cx) => (
            <Oeil key={cx} cx={cx} humeur={humeur} anime={anime} />
          ))}
          {humeur === 'inquiete' &&
            [undefined, MIROIR].map((t) => (
              <path key={t ?? 'gauche'} d={SOURCIL} transform={t} stroke={NUIT} strokeWidth={6} strokeLinecap="round" />
            ))}

          <Bec parle={humeur === 'parle'} anime={anime} />

          {/* Châssis et roues */}
          <rect {...CHASSIS} fill={NUIT} />
          {ROUES.map((x) => (
            <Roue key={x} cx={x} tourne={anime && humeur === 'parle'} />
          ))}

          {joie && (
            <>
              <Etincelle x={22} y={44} rayon={11} debut={0} anime={anime} />
              <Etincelle x={180} y={28} rayon={13} debut={0.3} anime={anime} />
              <Etincelle x={190} y={84} rayon={7} debut={0.6} anime={anime} />
            </>
          )}
          {humeur === 'inquiete' && <Goutte anime={anime} />}
        </g>
      </g>
    </svg>
  )
}
