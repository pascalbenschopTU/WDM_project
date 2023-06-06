rs.initiate(
    {
        _id: "rs-order_shard-02", 
        version: 1, 
        members: [ 
            { _id: 0, host: "order-shard02-a:28125" }, 
            { _id: 1, host: "order-shard02-b:28126" },
            //{ _id: 2, host: "order-shard02-b:28127" },
        ] 
    }
)