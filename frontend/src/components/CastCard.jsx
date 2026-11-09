import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const ROLE_LABEL = {
  director: "Director", hero: "Hero", heroine: "Heroine", villain: "Villain",
  music: "Music", cinematographer: "Cinematography", producer: "Producer",
};

export { ROLE_LABEL };

function Avatar({ src, name }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return (
      <div aria-hidden className="flex aspect-[3/4] w-full items-center justify-center bg-panel-2 text-2xl font-semibold text-muted">
        {name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
      </div>
    );
  }
  return (
    <img src={src} alt="" loading="lazy" onError={() => setFailed(true)}
         className="aspect-[3/4] w-full object-cover" />
  );
}

export default function CastCard({ person }) {
  return (
    <motion.div whileHover={{ y: -4 }} transition={{ duration: 0.15 }}>
      <Link
        to={`/person/${person.person_id}`}
        className="group block overflow-hidden rounded-xl border border-line bg-panel"
      >
        <div className="relative">
          <Avatar src={person.photo_url} name={person.name} />
          {/* Hover / keyboard-focus card with the character name */}
          {person.character_name && (
            <div className="absolute inset-x-0 bottom-0 translate-y-full bg-black/85 p-2 text-xs text-white transition-transform group-hover:translate-y-0 group-focus-visible:translate-y-0">
              as {person.character_name}
            </div>
          )}
        </div>
        <div className="p-2">
          <p className="truncate text-sm font-medium text-white">{person.name}</p>
          <p className="text-xs text-gold">{ROLE_LABEL[person.role] ?? person.role}</p>
        </div>
      </Link>
    </motion.div>
  );
}