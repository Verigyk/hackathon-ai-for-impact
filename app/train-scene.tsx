export function TrainScene() {
  return <svg viewBox="0 0 500 275" aria-hidden="true" className="train-scene">
    <defs><linearGradient id="train-paint" x1="0" x2="1"><stop stopColor="#5a237b"/><stop offset="1" stopColor="#bd1675"/></linearGradient><linearGradient id="window-paint" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#24213d"/><stop offset="1" stopColor="#535069"/></linearGradient></defs>
    <circle cx="345" cy="106" r="91" fill="#f7d3e8"/><circle cx="345" cy="106" r="64" fill="#fce9f3"/>
    <path d="M25 213Q125 172 205 193T480 182V260H25Z" fill="#dfd5ed"/>
    <path d="M50 234Q201 205 484 220" fill="none" stroke="#a68fbf" strokeWidth="3"/>
    <path d="M50 245Q201 216 484 231" fill="none" stroke="#a68fbf" strokeWidth="3"/>
    <g transform="translate(20 55) rotate(-3 230 130)"><path d="M36 60H350Q397 60 440 124L450 156H36Z" fill="url(#train-paint)"/><path d="M36 59H347Q364 59 379 69H36Z" fill="#faf9fc"/><path d="M36 135H443L450 156H36Z" fill="#eeeeF5"/><path d="M36 158H448" stroke="#50215f" strokeWidth="6"/>
      {[65,122,179,236,293].map(x=><rect key={x} x={x} y="80" width="40" height="33" rx="8" fill="url(#window-paint)"/>)}<path d="M359 78Q391 86 413 118H359Z" fill="url(#window-paint)"/><path d="M333 72V145" stroke="#ffffff" strokeOpacity=".65" strokeWidth="2"/>
      <circle cx="91" cy="162" r="12" fill="#393042"/><circle cx="317" cy="162" r="12" fill="#393042"/><circle cx="398" cy="162" r="12" fill="#393042"/><text x="179" y="135" fill="#fff" fontSize="20" fontWeight="800" fontFamily="Arial">liO</text>
    </g><g fill="#8561a4"><path d="M73 82V141H69V82Z"/><path d="M71 54L49 103H94Z"/><path d="M444 64V120H440V64Z"/><path d="M442 41L424 88H460Z"/></g>
    <circle cx="139" cy="38" r="5" fill="#bd1675"/><circle cx="467" cy="148" r="4" fill="#bd1675"/><path d="M226 21v14m-7-7h14" stroke="#ad86c6" strokeWidth="2"/>
  </svg>;
}
