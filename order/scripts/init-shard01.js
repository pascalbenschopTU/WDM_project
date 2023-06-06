rs.initiate(
    {
        _id: "rs-order_shard-01", 
        version: 1, 
        members: [ 
            { _id: 0, host: "order-shard01-a:28122" }, 
            { _id: 1, host: "order-shard01-b:28123" },
            //{ _id: 2, host: "order-shard01-c:28124" },
        ] 
    }
)