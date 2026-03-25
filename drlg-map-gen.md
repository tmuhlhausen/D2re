# D2 Network Packet Reference

All values little-endian. Packet command byte is always the first byte.
Server packets flow Game Server → Client. Client packets flow Client → Game Server.

---

## Client → Server Packets

| Cmd | Name | Length | Description |
|---|---|---|---|
| 0x01 | WalkToLocation | 5 | Walk to X,Y |
| 0x02 | WalkToEntity | 9 | Walk to unit (type+id) |
| 0x03 | RunToLocation | 5 | Run to X,Y |
| 0x04 | RunToEntity | 9 | Run to unit |
| 0x05 | LeftSkillOnLocation | 9 | Cast left skill at X,Y |
| 0x06 | LeftSkillOnEntity | 13 | Cast left skill on unit |
| 0x07 | LeftSkillOnEntityEx | 13 | Cast left skill on unit (repeated) |
| 0x08 | ShiftLeftSkillOnLocation | 9 | |
| 0x09 | ShiftLeftSkillOnEntity | 13 | |
| 0x0A | ShiftLeftSkillOnEntityEx | 13 | |
| 0x0C | RightSkillOnLocation | 9 | Cast right skill at X,Y |
| 0x0D | RightSkillOnEntity | 13 | Cast right skill on unit |
| 0x0E | RightSkillOnEntityEx | 13 | |
| 0x0F | ShiftRightSkillOnLocation | 9 | |
| 0x10 | ShiftRightSkillOnEntity | 13 | |
| 0x13 | InteractWithEntity | 9 | Interact / pick up item from ground |
| 0x14 | OverheadMessage | var | Say text overhead |
| 0x15 | ChatMessage | var | Chat message |
| 0x16 | PickupItem | 13 | Pick up item from ground |
| 0x17 | DropItem | 5 | Drop held item |
| 0x18 | DropGold | 9 | Drop gold |
| 0x19 | PickupGold | 9 | Pick up gold |
| 0x1A | ItemToCursor | 5 | Pick up item to cursor from inventory |
| 0x1C | IdentifyItem | 9 | Use scroll to ID item |
| 0x1D | UnshiftItem | 5 | |
| 0x20 | UseItem | 13 | Use item (potion, scroll, etc.) |
| 0x21 | InsertItem | var | Insert item into socket |
| 0x23 | SelectSkill | 9 | Assign skill to hand |
| 0x26 | Respawn | 1 | Respawn after death |
| 0x2F | GameLogon | var | Enter game world (initial sync) |
| 0x34 | NpcInit | 9 | Open NPC dialog |
| 0x38 | NpcBuy | var | Purchase item from NPC |
| 0x39 | NpcSell | var | Sell item to NPC |
| 0x3A | NpcIdentifyItems | 5 | Use Deckard Cain ID service |
| 0x3D | PingResponse | 5 | Respond to server ping |
| 0x50 | EnterPortal | 5 | Enter town portal / red portal |
| 0x58 | CharacterPhrase | 9 | Triggers character voice clip |
| 0x59 | UpdateStats | 1 | Request stat sync from server |
| 0x5D | QuestMessage | 13 | Quest-related trigger |

### Detailed Packet Structs

```c
#pragma pack(push, 1)

// 0x01 — Walk to location
typedef struct C_WalkToLocation {
    BYTE cmd;       // 0x01
    WORD wX;
    WORD wY;
} C_WalkToLocation;

// 0x13 — Interact with entity / pick up ground item
typedef struct C_InteractWithEntity {
    BYTE  cmd;          // 0x13
    DWORD dwEntityType; // UnitType enum
    DWORD dwEntityId;   // runtime GUID
} C_InteractWithEntity;

// 0x23 — Select skill for hand
typedef struct C_SelectSkill {
    BYTE  cmd;      // 0x23
    WORD  wSkillId;
    BYTE  bHand;    // 0 = left, 0x80 = right
    WORD  wItemId;  // FFFF if no item
    WORD  _pad;
} C_SelectSkill;

// 0x3D — Ping response (client replies with server's nonce)
typedef struct C_PingResponse {
    BYTE  cmd;      // 0x3D
    DWORD dwNonce;  // echoed from server ping packet
} C_PingResponse;

#pragma pack(pop)
```

---

## Server → Client Packets

| Cmd | Name | Length | Description |
|---|---|---|---|
| 0x01 | GameLoading | 1 | Game world is loading |
| 0x02 | GameFlags | 8 | Flags for current game (expansion, ladder, etc.) |
| 0x05 | UnitSkillList | var | Skills that a unit has |
| 0x06 | SetSkillHotkey | 6 | Assigns skill to hotkey slot |
| 0x07 | ItemWorldActionB1 | var | Item on ground (appear / pickup animation) |
| 0x08 | ItemWorldActionB2 | var | Item move/throw |
| 0x09 | ClearCursor | 1 | Clears cursor item client-side |
| 0x0A | Relator1 | 13 | Relationship update (party, town portal) |
| 0x0B | Relator2 | 13 | |
| 0x0F | HpMpUpdate | 5 | Fast HP/MP update for self |
| 0x15 | EventMessage | var | Chat / system message |
| 0x17 | AssignSkill | var | Assign skill to unit slot |
| 0x18 | ShowUnit | 12 | Reveal unit on map |
| 0x19 | QuestSpecialAction | var | Quest trigger (cain, pandemonium, etc.) |
| 0x1A | GameObjectAction | 13 | Object state change (door, chest, shrine) |
| 0x1D | NpcHit | var | NPC combat log entry |
| 0x1E | PlayerStop | 11 | Unit stops movement |
| 0x1F | ObjectStop | 11 | |
| 0x20 | UnitStop | 13 | Generic unit stop |
| 0x21 | UnitReanimate | 13 | Unit revived |
| 0x26 | RemoveObject | 9 | Remove unit from client |
| 0x27 | GameChat | var | Chat message in game |
| 0x28 | NpcMove | 11 | NPC walk target |
| 0x29 | NpcMoveToTarget | 16 | NPC moves toward entity |
| 0x2A | NpcState | 13 | NPC mode/state change |
| 0x2C | NpcAction | 16 | NPC performs action (attack, cast) |
| 0x2E | PlayerMove | 16 | Player walk |
| 0x2F | PlayerMoveToTarget | 21 | Player run to entity |
| 0x30 | PlayerState | 14 | Player mode change |
| 0x34 | PlayerStop2 | 13 | |
| 0x51 | LoadAct | 14 | Load new act data |
| 0x59 | ExperienceByteA | var | XP update |
| 0x5A | ExperienceWordA | var | XP update (word form) |
| 0x5B | ExperienceDWordA | var | XP update (dword form) |
| 0x5C | AttributeByteA | 4 | Stat update (byte) |
| 0x5D | AttributeWordA | 5 | Stat update (word) |
| 0x5E | AttributeDWordA | 7 | Stat update (dword) |
| 0x61 | StateNotification | var | Status effect applied/removed |
| 0x62 | GameHandshake | 4 | Initial connection ACK |
| 0x6D | UpdateItemStats | var | Full item stat block |
| 0x6E | UseItem | 9 | Item use confirmed |
| 0x77 | Pong | 5 | Server ping packet |
| 0x7A | DelayedState | var | State with delay |
| 0x81 | TradeAction | var | Trade protocol |
| 0x82 | TradeAccepted | 1 | Trade accepted by other party |
| 0x8F | AssignHotkey | 6 | |
| 0x95 | UnitAssign | var | Assign entity to client (full init) |
| 0x96 | ReassignPlayer | 11 | |
| 0x97 | MultiUnitAssign | var | Multiple unit assignments |
| 0x9B | NpcInfo | var | NPC dialog content |
| 0x9C | TownPortalState | 8 | Portal opened/closed |

### Detailed Packet Structs

```c
#pragma pack(push, 1)

// 0x0F — HP/MP fast update
typedef struct S_HpMpUpdate {
    BYTE cmd;       // 0x0F
    WORD wHpPct;    // (curHP / maxHP) * 32768
    WORD wMpPct;    // (curMP / maxMP) * 32768
} S_HpMpUpdate;

// 0x5C — Attribute update (byte encoding)
typedef struct S_AttributeByteA {
    BYTE cmd;       // 0x5C
    WORD wStatId;   // STAT_* enum
    BYTE bValue;    // new value
} S_AttributeByteA;

// 0x5D — Attribute update (word encoding)
typedef struct S_AttributeWordA {
    BYTE cmd;
    WORD wStatId;
    WORD wValue;
} S_AttributeWordA;

// 0x5E — Attribute update (dword encoding)
typedef struct S_AttributeDWordA {
    BYTE  cmd;
    WORD  wStatId;
    DWORD dwValue;
} S_AttributeDWordA;

// 0x77 — Ping (server sends, client echoes with 0x3D)
typedef struct S_Ping {
    BYTE  cmd;      // 0x77
    DWORD dwNonce;
} S_Ping;

// 0x95 — Unit assignment header (variable body follows)
typedef struct S_UnitAssign_Header {
    BYTE  cmd;          // 0x95
    BYTE  bUnitType;    // UnitType enum
    DWORD dwClassId;    // class/npc/item ID
    DWORD dwUnitId;     // runtime GUID
    DWORD dwMode;       // animation mode
    WORD  wX;
    WORD  wY;
    // BYTE bLife — for monsters: HP% encoded as value/128
    // Additional variable data follows depending on bUnitType
} S_UnitAssign_Header;

#pragma pack(pop)
```
