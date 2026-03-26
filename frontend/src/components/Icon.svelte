<script>
  export let name;
  export let size = 20;
  export let strokeWidth = 1.8;
  export let className = "";

  const icons = {
    default: [{ d: "M5 5h14v14H5z" }, { d: "M5 12h14" }, { d: "M12 5v14" }],
    mission: [{ d: "M3 11.5L12 4l9 7.5" }, { d: "M5.5 10.5V20h13V10.5" }],
    pending: [
      { d: "M12 5v12" },
      { d: "M7.5 9.5L12 5l4.5 4.5" },
      { d: "M7 17h10" },
    ],
    compliance: [
      { d: "M12 4l7 2.5v5c0 4.5-3 8.5-7 9.5-4-1-7-5-7-9.5v-5z" },
      { d: "M9 11l2 2 4-4" },
    ],
    risk: [{ d: "M12 5l8 14H4z" }, { d: "M12 10.5v4" }, { d: "M12 17.5h.01" }],
    reports: [
      {
        d: "M6 7h12a1 1 0 011 1v10a1 1 0 01-1 1H6a1 1 0 01-1-1V8a1 1 0 011-1z",
      },
      { d: "M8 4v3" },
      { d: "M16 4v3" },
      { d: "M5 11h14" },
    ],
    audit: [
      { d: "M9 5h6" },
      {
        d: "M7 5h10a1 1 0 011 1v12a1 1 0 01-1 1H7a1 1 0 01-1-1V6a1 1 0 011-1z",
      },
      { d: "M9 9h6" },
      { d: "M9 13h6" },
    ],
    field: [
      { d: "M12 5a4 4 0 014 4c0 4-4 8-4 8s-4-4-4-8a4 4 0 014-4z" },
      { d: "M12 9.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3z" },
    ],
    analytics: [
      { d: "M4 19h16" },
      { d: "M8 19v-5" },
      { d: "M12 19V9" },
      { d: "M16 19V5" },
    ],
    dashboard: [
      { d: "M4 13h6v7H4z" },
      { d: "M14 4h6v16h-6z" },
      { d: "M10 7h4v13h-4z" },
    ],
    folder: [
      { d: "M3 7h6l2 3h10v9a2 2 0 01-2 2H5a2 2 0 01-2-2z" },
      { d: "M3 7V5a2 2 0 012-2h5l2 3" },
    ],
    tasks: [
      { d: "M6 6h12v12H6z" },
      { d: "M9 9h6" },
      { d: "M9 13h6" },
      { d: "M9 17h3" },
    ],
    budget: [{ d: "M12 12V4a8 8 0 110 8z" }, { d: "M12 12H4a8 8 0 018 8z" }],
    bell: [
      { d: "M18 15V9a6 6 0 10-12 0v6" },
      { d: "M5 15h14" },
      { d: "M10 19h4" },
    ],
    money: [{ d: "M4 7h16v10H4z" }, { d: "M7 12h10" }, { d: "M12 9v6" }],
    exchange: [
      { d: "M7 5l-3 3 3 3" },
      { d: "M17 19l3-3-3-3" },
      { d: "M4 8h16" },
      { d: "M4 16h16" },
    ],
    approvals: [{ d: "M5 12.5L9 17l10-10" }],
    documentCheck: [
      { d: "M9 4h6l3 3v11a2 2 0 01-2 2H9a2 2 0 01-2-2V6a2 2 0 012-2z" },
      { d: "M15 4v4h4" },
      { d: "M10 13l2 2 3-4" },
    ],
    statusOn: [{ d: "M12 6a6 6 0 110 12 6 6 0 010-12z" }],
    statusWarn: [
      { d: "M12 6a6 6 0 110 12 6 6 0 010-12z" },
      { d: "M12 9v3.5" },
      { d: "M12 15h.01" },
    ],
    statusCritical: [
      { d: "M12 6a6 6 0 110 12 6 6 0 010-12z" },
      { d: "M9.5 9.5l5 5" },
      { d: "M14.5 9.5l-5 5" },
    ],
    users: [
      { d: "M8 11a3 3 0 100-6 3 3 0 000 6z" },
      { d: "M16 12a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" },
      { d: "M4 19v-1a4 4 0 014-4h2a4 4 0 014 4v1" },
      { d: "M14 19v-1a3 3 0 013-3h1" },
    ],
    search: [
      { d: "M11 5a6 6 0 100 12 6 6 0 000-12z" },
      { d: "M16.5 16.5L21 21" },
    ],
    warning: [
      { d: "M12 5l8 14H4z" },
      { d: "M12 10.5v4" },
      { d: "M12 17.5h.01" },
    ],
    document: [
      { d: "M9 4h6l3 3v11a2 2 0 01-2 2H9a2 2 0 01-2-2V6a2 2 0 012-2z" },
      { d: "M15 4v4h4" },
      { d: "M9 12h6" },
      { d: "M9 16h6" },
    ],
    auditPackage: [
      { d: "M5 7h14l-2 10H7z" },
      { d: "M9 11h6" },
      { d: "M10 15h4" },
    ],
    rocket: [
      {
        d: "M12 3c2 2 3.5 4.5 3.5 7.5a5.5 5.5 0 01-7 5.25L6 18l2.25-2.25A5.5 5.5 0 018.5 10.5C8.5 7.5 10 5 12 3z",
      },
      { d: "M12 8.5a2 2 0 110 4 2 2 0 010-4z" },
      { d: "M6 18l-2 3 3-2" },
    ],
    info: [
      { d: "M12 11h.01" },
      { d: "M12 7h.01" },
      { d: "M11 11h1v4h1" },
      { d: "M12 22a10 10 0 110-20 10 10 0 010 20z" },
    ],
    setting: [
      { d: "M12 15a3 3 0 100-6 3 3 0 000 6z" },
      { d: "M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2h-4a2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 001.51-1H3a2 2 0 01-2-2V9a2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82 1.65 1.65 0 001.51 1H9V3a2 2 0 012-2h4a2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82 1.65 1.65 0 001.51 1H21a2 2 0 012 2v4a2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" }
    ],
  };

  const segments = icons[name] ?? icons.default;
</script>

<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 24 24"
  width={size}
  height={size}
  fill="none"
  stroke="currentColor"
  stroke-width={strokeWidth}
  class={className}
  aria-hidden="true"
>
  {#each segments as segment}
    <path
      d={segment.d}
      stroke-linecap={segment.cap ?? "round"}
      stroke-linejoin={segment.join ?? "round"}
      fill={segment.fill ?? "none"}
      stroke={segment.stroke ?? "currentColor"}
    />
  {/each}
</svg>
