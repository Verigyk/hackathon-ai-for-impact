export function Landscape({ art = 'castle', variant = 'ochre', hero = false }: { art?: string; variant?: string; hero?: boolean }) {
  const colors: Record<string, [string, string, string]> = { ochre: ['#eee0c4','#ba7345','#385d56'], brick: ['#edd6c5','#af6f59','#57736c'], rose: ['#eedbd5','#bc8170','#4e7169'], sage: ['#dbe6d7','#668c77','#d8a572'], sand: ['#e8ddc7','#b78b5e','#57736c'] };
  const [sky, building, leaf] = colors[variant] || colors.ochre;
  return <svg viewBox="0 0 640 330" aria-hidden="true" className={hero ? 'hero-art' : 'landscape'}>
    <rect width="640" height="330" fill={sky}/><circle cx="485" cy="68" r="34" fill="#f7f0d8"/>
    <path d="M0 216 Q100 132 223 224 Q365 131 482 194 Q561 137 640 187 L640 330 H0Z" fill={leaf} opacity=".22"/>
    <path d="M0 274 Q152 218 288 269 Q462 217 640 264 V330 H0Z" fill={leaf} opacity=".22"/>
    <path d="M100 293 Q270 240 611 300" fill="none" stroke="#f8f3e8" strokeWidth="24"/>
    {art === 'castle' || art === 'cathedral' ? <g fill={building}>
      <path d="M199 230V148H233V134H252V148H282V125H300V147H330V130H348V147H378V133H396V148H424V230Z"/>
      <path d="M171 230V107H212V230M410 230V96H450V230"/>
      <path d="M165 109L191 69L219 109M404 98L429 53L457 98" fill={leaf}/>
      <path d="M267 230V201Q286 177 305 201V230" fill={sky}/>
      {[185, 224, 320, 374, 424].map((x, i) => <rect key={x} x={x} y={i%2 ? 169 : 135} width="10" height="25" rx="5" fill={sky} opacity=".7"/>)}
    </g> : art === 'arena' ? <g><ellipse cx="317" cy="223" rx="137" ry="25" fill={building}/><path d="M180 218V155Q316 114 454 155V218Z" fill={building}/>{[200,230,260,290,320,350,380,410,440].map(x=><path key={x} d={`M${x} 204v-32q8-12 16 0v32z`} fill={sky}/>)}<path d="M179 158Q314 120 454 158" fill="none" stroke={leaf} strokeWidth="6"/></g> : <g fill={building}>
      {[175,235,295,355,415].map((x,i)=><g key={x}><path d={`M${x} 236V${151+i%2*25}L${x+25} ${126+i%2*25}L${x+50} ${151+i%2*25}V236Z`}/>{[0,1,2].map(y=><rect key={y} x={x+20} y={158+y*24} width="11" height="15" fill={sky}/>)}</g>)}
    </g>}
    <g fill={leaf}><path d="M92 247V180M528 254V184" stroke={leaf} strokeWidth="6"/>
    <ellipse cx="91" cy="180" rx="32" ry="44"/><ellipse cx="529" cy="188" rx="29" ry="40"/><path d="M32 292Q44 261 69 284Q61 265 83 272V303H28Z"/></g>
    {hero && <g><path d="M0 300L640 300" stroke="#a7b8a7" strokeWidth="4"/><g transform="translate(120 268)"><rect width="165" height="26" rx="13" fill="#de6a42"/><path d="M4 20H161V26H4Z" fill="#eee7d9"/>{[20,45,70,95,120].map(x=><rect key={x} x={x} y="5" width="15" height="10" rx="3" fill="#f8eedb"/>)}<circle cx="32" cy="28" r="4" fill="#294c43"/><circle cx="137" cy="28" r="4" fill="#294c43"/></g></g>}
    <path d="M80 69q12-10 24 0m417 54q9-9 18 0" fill="none" stroke={leaf} strokeWidth="2" opacity=".65"/>
  </svg>;
}

export function RegionMap() {
  return <svg viewBox="0 0 320 225" role="img" aria-label="Carte illustrative des destinations en Occitanie">
    <path d="M26 62L78 24L135 32L160 12L211 43L226 38L248 79L292 111L272 160L227 169L200 199L143 178L114 209L83 170L35 163L49 114Z" fill="#e5eade" stroke="#b7c6b3" strokeWidth="1.5"/>
    <path d="M95 121Q139 91 158 147Q200 161 240 110M95 121Q116 89 146 79" fill="none" stroke="#d37851" strokeDasharray="4 4" strokeWidth="2"/>
    {[['Toulouse',95,121],['Albi',146,79],['Carcassonne',158,147],['Montpellier',240,110]].map(([s,x,y])=><g key={s as string}><circle cx={x} cy={y} r="4" fill="#2d5e51"/><text x={Number(x)+7} y={Number(y)-7} fill="#395b50" fontSize="11" fontFamily="sans-serif">{s}</text></g>)}
    <text x="211" y="201" fill="#91afa8" fontSize="11" fontFamily="serif" fontStyle="italic">Méditerranée</text>
  </svg>;
}
