export type Cam={
 id:string;
 name:string;
 status:string;
 enabled:boolean;
 city?:string|null;
 state?:string|null;
 country?:string|null;
 latitude?:number|null;
 longitude?:number|null;
 feed_kind?:string;
 source_url?:string|null;
 attribution?:string|null;
 refresh_seconds?:number|null;
 last_checked_at?:string|null;
 last_image_at?:string|null;
};
