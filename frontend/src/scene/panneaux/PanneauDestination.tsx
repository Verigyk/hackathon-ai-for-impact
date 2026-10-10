import { useId, useState } from 'react'
import type { ReactNode } from 'react'
import { Bus, Compass, Gauge, Footprints, MapPin, TrainFront } from 'lucide-react'
import type { PropsPanneau } from '../types'
import { AnneauScore } from '../../components/voyage/IndiceConfiance'
import PastilleNiveau from '../../components/voyage/PastilleNiveau'
import { formaterDuree, libelleCorrespondances } from '../../components/voyage/format'
import { CadrePanneau, DetailPourquoi, PanneauVide, SqueletteCarte } from './communs'
import { LIBELLES_ACCES, LIBELLES_INDICE } from './libelles'

/** Au-delà, le texte pédagogique est replié sur deux lignes avec un bouton « Tout lire ». */
const LONGUEUR_REPLIABLE = 150

function Indicateur({ icone, libelle, children }: { icone: ReactNode; libelle: string; children: ReactNode }) {
  return (
    <div className="grid min-w-0 grid-cols-[6rem_minmax(0,1fr)] items-center gap-3 rounded-field bg-base-200 p-3 @lg:flex @lg:flex-col @lg:items-start @lg:gap-1.5">
      <p className="flex items-center gap-1.5 text-xs font-semibold text-base-content/70">
        {icone}
        {libelle}
      </p>
      <div className="flex min-w-0 flex-col items-start gap-1.5">{children}</div>
    </div>
  )
}

/** Étape « destination » : UNE grande carte sobre. Les badges de source sont déjà sous la bulle de Tchouette. */
export default function PanneauDestination({ reponse, chargement }: PropsPanneau) {
  const titreId = useId()
  const [toutLire, setToutLire] = useState(false)
  const destination = reponse.destination

  if (!destination) {
    return chargement ? (
      <SqueletteCarte />
    ) : (
      <PanneauVide
        titre="Pas encore de destination à vous montrer"
        texte="Précisez votre projet à Tchouette, ou revenez à l’étape précédente avec « Retour »."
      />
    )
  }

  const { acces_gare_site: acces } = destination
  const IconeAcces = acces.mode === 'pied' ? Footprints : Bus
  const depart = reponse.etat.demande.gare_depart?.nom ?? reponse.etat.demande.lieu_depart?.libelle ?? null
  const decouverte = destination.site_id.startsWith('dt-')
  const interet = destination.interet_pedagogique
  const replie = interet.length > LONGUEUR_REPLIABLE && !toutLire

  return (
    <div className="flex min-w-0 flex-col gap-3">
      <CadrePanneau titreId={titreId} occupe={chargement}>
        <div className="@container flex flex-col gap-4 p-4 sm:p-5">
          <header className="flex min-w-0 flex-col gap-1.5 pe-10">
            {decouverte && (
              <span className="badge badge-accent badge-sm w-fit gap-1 font-bold">
                <Compass className="size-3.5" aria-hidden="true" />
                Découverte
              </span>
            )}
            <h2 id={titreId} className="text-xl font-bold leading-tight">
              {destination.nom}
            </h2>
            <p className="flex flex-wrap items-center gap-x-1.5 text-sm">
              <MapPin className="size-4 shrink-0" aria-hidden="true" />
              <span className="font-semibold">{destination.commune}</span>
              <span aria-hidden="true">·</span>
              <span>Gare : {destination.gare.nom}</span>
            </p>
          </header>

          <div className="grid gap-1">
            <p className={replie ? 'line-clamp-2 text-sm leading-relaxed' : 'text-sm leading-relaxed'}>{interet}</p>
            {interet.length > LONGUEUR_REPLIABLE && (
              <button
                type="button"
                onClick={() => setToutLire((v) => !v)}
                aria-expanded={toutLire}
                className="btn btn-ghost btn-sm min-h-10 w-fit px-2 text-secondary"
              >
                {toutLire ? 'Réduire' : 'Tout lire'}
              </button>
            )}
          </div>

          {decouverte && (
            <p role="note" className="rounded-field border-2 border-dashed border-accent bg-accent/15 p-2.5 text-sm">
              <span className="font-bold">À vérifier : </span>
              horaires et accueil de groupe à vérifier auprès du site.
            </p>
          )}

          <div className="grid gap-2 border-t-2 border-dashed border-base-300 pt-4 @lg:grid-cols-3">
            <Indicateur icone={<TrainFront className="size-3.5 shrink-0" aria-hidden="true" />} libelle="Trajet">
              <p className="text-lg font-extrabold leading-none tabular-nums">
                {formaterDuree(destination.temps_trajet_min)}
              </p>
              <p className="text-xs leading-snug">
                {libelleCorrespondances(destination.correspondances)}
                {depart && <span className="block">depuis {depart}</span>}
              </p>
            </Indicateur>

            <Indicateur icone={<IconeAcces className="size-3.5 shrink-0" aria-hidden="true" />} libelle="Gare → site">
              <p className="text-lg font-extrabold leading-none tabular-nums">
                {acces.minutes_groupe}
                <span className="text-xs font-semibold"> min</span>
              </p>
              <p className="text-xs leading-snug">{acces.mode === 'pied' ? 'à pied' : 'en transport urbain'}</p>
              <PastilleNiveau niveau={acces.niveau} libelle={LIBELLES_ACCES[acces.niveau]} />
            </Indicateur>

            <Indicateur icone={<Gauge className="size-3.5 shrink-0" aria-hidden="true" />} libelle="Confiance">
              <AnneauScore score={destination.indice_confiance} niveau={destination.niveau} />
              <PastilleNiveau niveau={destination.niveau} libelle={LIBELLES_INDICE[destination.niveau]} />
            </Indicateur>
          </div>
        </div>
      </CadrePanneau>

      {reponse.detail && <DetailPourquoi key={reponse.detail.titre} detail={reponse.detail} titre="Pourquoi ce choix ?" />}
    </div>
  )
}
